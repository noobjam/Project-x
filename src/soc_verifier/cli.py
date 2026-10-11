"""Composition root: CLI wiring is the only place that selects concrete adapters."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

import httpx
import typer
from langchain_core.runnables import RunnableConfig
from pydantic import ValidationError

from soc_verifier.domain.models import PlanReview, SpecAnalysis, Specification, VerificationPlan
from soc_verifier.export.xlsx import export_plan
from soc_verifier.ingestion.docx import ingest_docx
from soc_verifier.llm.openrouter import ModelResponseError, OpenRouterLLM
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore
from soc_verifier.storage.checkpoints import checkpoint_store
from soc_verifier.workflows.spec_to_plan.graph import PlanState, build_graph
from soc_verifier.workflows.spec_to_plan.prompts import PROMPT_VERSION

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
    """Send an extracted specification to the configured model and create a draft plan."""
    with _errors():
        settings = Settings()
        settings.require_llm()
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
        _execute(settings, run_id, artifacts, {"specification": spec.model_dump(mode="json")})


@app.command()
def resume(run_id: Annotated[str, typer.Argument()]) -> None:
    """Resume an interrupted run using its persisted graph checkpoints."""
    with _errors():
        run_id = str(UUID(run_id))
        settings = Settings()
        settings.require_llm()
        root = settings.artifact_dir / "runs" / run_id
        if not root.is_dir():
            raise ValueError("Unknown run ID")
        artifacts = ArtifactStore(root)
        manifest = artifacts.read("manifest.json")
        if manifest["prompt_version"] != PROMPT_VERSION or any(
            manifest[key] != value for key, value in _run_configuration(settings).items()
        ):
            raise ValueError("Run configuration changed; restore its settings or start a new run")
        _execute(settings, run_id, artifacts, None)


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
            analysis=SpecAnalysis.model_validate(artifacts.read("analysis.json")),
            plan=VerificationPlan.model_validate(artifacts.read(result["plan_artifact"])),
            review=PlanReview.model_validate(artifacts.read(result["review_artifact"])),
        )
        typer.echo(f"Exported draft verification plan to {output}")


def _run_configuration(settings: Settings) -> dict[str, Any]:
    return {
        "model": settings.model,
        "provider": settings.provider,
        "max_revisions": settings.max_revisions,
        "max_output_tokens": settings.max_output_tokens,
        "max_input_characters": settings.max_input_characters,
    }


def _execute(
    settings: Settings,
    run_id: str,
    artifacts: ArtifactStore,
    initial: PlanState | None,
) -> None:
    config: RunnableConfig = {
        "configurable": {"thread_id": run_id},
        "recursion_limit": 2 * settings.max_revisions + 8,
    }
    handler = logging.FileHandler(artifacts.path("events.log"), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger = logging.getLogger("soc_verifier")
    previous_level = logger.level
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        with checkpoint_store(settings) as checkpoints, httpx.Client() as client:
            graph = build_graph(
                OpenRouterLLM(settings, client),
                artifacts,
                checkpoints,
                max_revisions=settings.max_revisions,
            )
            snapshot = graph.get_state(config)
            if initial is None and not snapshot.values:
                # A failure before the first checkpoint can still recover from local input.
                initial = {"specification": artifacts.read("specification.json")}
            if initial is None and not snapshot.next:
                typer.echo(f"Run already completed: {artifacts.root}")
                return
            result = graph.invoke(initial, config, durability="sync")
            typer.echo(f"Status: {result['status']}; artifacts: {artifacts.root}")
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        handler.close()
