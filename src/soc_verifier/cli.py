"""Composition root: CLI wiring is the only place that selects concrete adapters."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from time import sleep
from typing import Annotated, Any
from uuid import UUID, uuid4

import httpx
import typer
from pydantic import ValidationError

from soc_verifier.agents.base import ModelResponseError
from soc_verifier.agents.instructions import PROMPT_VERSION
from soc_verifier.agents.runtime import AgentRuntime
from soc_verifier.domain.models import PlanReview, SpecAnalysis, Specification, VerificationPlan
from soc_verifier.export.xlsx import export_plan
from soc_verifier.ingestion.docx import ingest_docx
from soc_verifier.providers.budget import read_spending
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.workflows.spec_to_plan.workflow import PlanningWorkflow

app = typer.Typer(no_args_is_help=True, help="Traceable system-level verification workflows.")


@contextmanager
def _errors() -> Iterator[None]:
    try:
        yield
    except ValidationError as error:
        # ValidationError.__str__ can expose source text or model response fragments.
        typer.echo(f"Schema validation failed ({error.error_count()} errors).", err=True)
        raise typer.Exit(1) from None
    except (ValueError, OSError, ModelResponseError, RuntimeError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from None
    except httpx.HTTPError as error:
        status = (
            error.response.status_code if isinstance(error, httpx.HTTPStatusError) else "network"
        )
        typer.echo(f"Model request failed ({status}); saved runs can be resumed.", err=True)
        raise typer.Exit(1) from None


@app.command()
def ingest(
    source: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("artifacts/specification.json"),
) -> None:
    """Extract a DOCX locally. This command never calls a model."""
    with _errors():
        spec = ingest_docx(source)
        ArtifactStore(output.parent).write(output.name, spec)
        typer.echo(f"Extracted {len(spec.blocks)} blocks to {output}")
        for warning in spec.extraction_warnings:
            typer.echo(f"Warning: {warning}")


@app.command()
def plan(
    specification: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
) -> None:
    """Run the analyst, planner and reviewer agents on an extracted specification."""
    with _errors():
        settings = Settings()
        settings.require_agents()
        spec = Specification.model_validate_json(specification.read_text(encoding="utf-8"))
        run_id = str(uuid4())
        artifacts = ArtifactStore(settings.artifact_dir / "runs" / run_id)
        artifacts.write("specification.json", spec)
        artifacts.write(
            "manifest.json",
            {
                "schema_version": "1.0",
                "run_id": run_id,
                "created_at": datetime.now(UTC).isoformat(),
                "specification_sha256": spec.sha256,
                "prompt_version": PROMPT_VERSION,
                **_run_configuration(settings),
            },
        )
        typer.echo(f"Run: {run_id}")
        _execute(settings, artifacts, resuming=False)


@app.command()
def resume(
    run_id: Annotated[str, typer.Argument()],
    workers: Annotated[int | None, typer.Option("--workers", min=1, max=8)] = None,
    max_output_tokens: Annotated[
        int | None, typer.Option("--max-output-tokens", min=256, max=64_000)
    ] = None,
) -> None:
    """Resume an interrupted run using its validated artifact checkpoints."""
    with _errors():
        run_id = str(UUID(run_id))
        settings = Settings()
        settings.require_agents()
        root = settings.artifact_dir / "runs" / run_id
        if not root.is_dir():
            raise ValueError("Unknown run ID")
        artifacts = ArtifactStore(root)
        manifest = artifacts.read("manifest.json")
        if (
            manifest.get("engine") != "openai-agents-v1"
            or manifest["prompt_version"] != PROMPT_VERSION
            or any(
                manifest.get(key) != value for key, value in _run_configuration(settings).items()
            )
        ):
            raise ValueError("Run configuration changed; restore its settings or start a new run")
        # Scheduling does not change prompts, partitions, or artifact identities.
        # Keep the original manifest intact and log the effective worker count.
        if workers is not None:
            settings = settings.model_copy(update={"batch_workers": workers})
        if max_output_tokens is not None:
            if max_output_tokens > settings.max_output_tokens:
                raise ValueError("Resume output-token override may only lower the original limit")
            settings = settings.model_copy(update={"max_output_tokens": max_output_tokens})
        _execute(settings, artifacts, resuming=True)


@app.command()
def spend(
    run_id: Annotated[str, typer.Argument()],
    watch: Annotated[
        bool, typer.Option("--watch", help="Refresh every five seconds; Ctrl-C stops.")
    ] = False,
) -> None:
    """Show run spending locally, without API calls or credentials."""
    with _errors():
        root = Settings().artifact_dir / "runs" / str(UUID(run_id))
        if not root.is_dir():
            raise ValueError("Unknown run ID")
        artifacts = ArtifactStore(root)
        manifest = artifacts.read("manifest.json")
        if "max_cost_usd" not in manifest:
            raise ValueError("This legacy run has no cost ledger; check its usage in events.log")
        limit = Decimal(str(manifest["max_cost_usd"]))
        typer.echo(f"Run: {root.name}; budget ${limit:.2f}; model {manifest['model']}")
        typer.echo("Reserved includes in-flight or unknown charges; it is not reported spend.")
        while True:
            snapshot = read_spending(artifacts)
            remaining = max(Decimal(0), limit - snapshot.committed)
            now = datetime.now(UTC).strftime("%H:%M:%S UTC")
            typer.echo(
                f"{now} | Reported ${snapshot.reported:.6f} | "
                f"Reserved ${snapshot.reserved:.6f} ({snapshot.unsettled_calls} unsettled) | "
                f"Budget available ${remaining:.6f} | "
                f"Attempts {snapshot.attempts}/{manifest['max_model_calls']}"
            )
            if artifacts.exists("budget-stopped.json"):
                typer.echo("Run stopped after a provider pricing violation.")
                return
            if artifacts.exists("result.json"):
                typer.echo(f"Run completed: {artifacts.read('result.json')['status']}")
                return
            if not watch:
                return
            sleep(5)


@app.command("export")
def export_command(
    run_id: Annotated[str, typer.Argument()],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path(
        "artifacts/verification_plan.xlsx"
    ),
) -> None:
    """Export a completed run's canonical artifacts to a review workbook, without API calls."""
    with _errors():
        root = Settings().artifact_dir / "runs" / str(UUID(run_id))
        if not root.is_dir():
            raise ValueError("Unknown run ID")
        artifacts = ArtifactStore(root)
        result = artifacts.read("result.json")
        export_plan(
            output,
            specification=Specification.model_validate(artifacts.read("specification.json")),
            analysis=SpecAnalysis.model_validate(
                artifacts.read(result.get("analysis_artifact", "analysis.json"))
            ),
            plan=VerificationPlan.model_validate(artifacts.read(result["plan_artifact"])),
            review=PlanReview.model_validate(artifacts.read(result["review_artifact"])),
        )
        typer.echo(f"Exported draft verification plan to {output}")


def _run_configuration(settings: Settings) -> dict[str, Any]:
    return {
        "engine": "openai-agents-v1",
        "agent_max_turns": settings.agent_max_turns,
        "model": settings.model,
        "provider": settings.provider,
        "max_revisions": settings.max_revisions,
        "max_output_tokens": settings.max_output_tokens,
        "max_input_characters": settings.max_input_characters,
        "chunk_max_characters": settings.chunk_max_characters,
        "plan_batch_size": settings.plan_batch_size,
        "batch_workers": settings.batch_workers,
        "max_model_calls": settings.max_model_calls,
        "max_cost_usd": settings.max_cost_usd,
    }


def _execute(
    settings: Settings,
    artifacts: ArtifactStore,
    *,
    resuming: bool,
) -> None:
    handler = logging.FileHandler(artifacts.path("events.log"), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger = logging.getLogger("soc_verifier")
    previous_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        logger.info(
            "execution workers=%s max_output_tokens=%s resume=%s",
            settings.batch_workers,
            settings.max_output_tokens,
            resuming,
        )
        if artifacts.exists("result.json"):
            typer.echo(f"Run already completed: {artifacts.root}")
            return
        with httpx.Client() as client:
            workflow = PlanningWorkflow(
                AgentRuntime(settings, client, artifacts=artifacts),
                artifacts,
                max_revisions=settings.max_revisions,
                chunk_max_characters=settings.chunk_max_characters,
                plan_batch_size=settings.plan_batch_size,
                batch_workers=settings.batch_workers,
            )
            result = workflow.run()
            typer.echo(f"Status: {result['status']}; artifacts: {artifacts.root}")
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        handler.close()
