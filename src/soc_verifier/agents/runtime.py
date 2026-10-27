"""Run actual SDK agents, with bounded tool loops and an OpenRouter model gateway."""

import asyncio
import logging
from uuid import uuid4

import httpx
from agents import (
    MaxTurnsExceeded,
    ModelBehaviorError,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
)
from openai import APIConnectionError, AsyncOpenAI
from pydantic import BaseModel

from soc_verifier.agents.analyst import create_analyst
from soc_verifier.agents.attempts import Invocation, current_invocation
from soc_verifier.agents.base import AgentRole, ModelResponseError
from soc_verifier.agents.planner import create_planner
from soc_verifier.agents.reviewer import create_reviewer
from soc_verifier.agents.tasks import (
    ArtifactReference,
    Task,
    TaskEnvelope,
    TaskInputs,
    fingerprint,
    runtime_versions,
)
from soc_verifier.agents.tools import EvidenceContext
from soc_verifier.domain.models import SpecAnalysis, Specification, VerificationPlan
from soc_verifier.providers.openrouter import OpenRouterTransport
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore

logger = logging.getLogger(__name__)


class AgentRuntime:
    def __init__(
        self, settings: Settings, client: httpx.Client, *, artifacts: ArtifactStore
    ) -> None:
        self.settings = settings
        self.artifacts = artifacts
        self.transport = OpenRouterTransport(settings, client, artifacts=artifacts)

    @property
    def configuration(self) -> dict[str, object]:
        return self.settings.agent_configuration()

    def _evidence(self, task: TaskEnvelope) -> EvidenceContext:
        references = task.inputs.evidence
        source = references["source"].read(self.artifacts)
        analysis = references["analysis"].read(self.artifacts) if "analysis" in references else None
        plan = references["plan"].read(self.artifacts) if "plan" in references else None
        for reference in references.values():
            reference.read(self.artifacts)
        return EvidenceContext(
            Specification.model_validate(source),
            SpecAnalysis.model_validate(analysis) if analysis is not None else None,
            VerificationPlan.model_validate(plan) if plan is not None else None,
        )

    def run[T: BaseModel](
        self,
        *,
        role: AgentRole,
        instruction: str,
        context: str,
        schema: type[T],
        task: TaskEnvelope | None = None,
    ) -> T:
        # Standalone SDK calls receive their own source-only task. Workflow calls
        # always supply exact evidence snapshots, including analysis/plan revisions.
        direct: Task | None = None
        if task is None:
            direct = Task.bind(
                self.artifacts,
                f"direct.{uuid4()}.json",
                TaskInputs(
                    role=role,
                    stage="direct",
                    assigned_ids=[],
                    evidence={
                        "source": ArtifactReference.capture(self.artifacts, "specification.json")
                    },
                    input_sha256=fingerprint(context),
                    instruction_sha256=fingerprint(instruction),
                    schema_sha256=fingerprint(schema.model_json_schema()),
                    versions=runtime_versions(),
                    configuration={"configuration": self.configuration},
                ),
            )
            task = direct.envelope
        if (
            task.inputs.role != role
            or task.inputs.instruction_sha256 != fingerprint(instruction)
            or task.inputs.schema_sha256 != fingerprint(schema.model_json_schema())
            or task.inputs.versions != runtime_versions()
            or task.inputs.configuration.get("configuration") != self.configuration
        ):
            raise ValueError("Agent request does not match its task configuration")
        invocation = Invocation(task, str(uuid4()))
        stem = f"invocation.{invocation.invocation_id}"
        self.artifacts.write(
            f"{stem}.json",
            {
                "format": "agent-invocation-v1",
                **invocation.attribution(),
                "context_sha256": fingerprint(context),
                "instruction_sha256": fingerprint(instruction),
                "schema_sha256": fingerprint(schema.model_json_schema()),
            },
        )
        token = current_invocation.set(invocation)
        try:
            result = asyncio.run(
                self._run(
                    role=role,
                    instruction=instruction,
                    context=context,
                    schema=schema,
                    task=task,
                )
            )
            if direct is not None:
                direct.save(result)
        except Exception as error:
            self.artifacts.write(
                f"{stem}.result.json",
                {
                    "format": "agent-invocation-result-v1",
                    **invocation.attribution(),
                    "status": "failed",
                    "error_type": type(error).__name__,
                    "calls": invocation.calls,
                },
            )
            raise
        else:
            self.artifacts.write(
                f"{stem}.result.json",
                {
                    "format": "agent-invocation-result-v1",
                    **invocation.attribution(),
                    "status": "returned",
                    "calls": invocation.calls,
                    "output_sha256": fingerprint(result),
                },
            )
            return result
        finally:
            current_invocation.reset(token)

    async def _run[T: BaseModel](
        self,
        *,
        role: AgentRole,
        instruction: str,
        context: str,
        schema: type[T],
        task: TaskEnvelope,
    ) -> T:
        assert self.settings.openrouter_api_key is not None
        async with AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.settings.openrouter_api_key.get_secret_value(),
            max_retries=0,
            http_client=httpx.AsyncClient(transport=self.transport),
        ) as client:
            model = OpenAIChatCompletionsModel(model=self.settings.model, openai_client=client)
            factory = {
                "analyst": create_analyst,
                "planner": create_planner,
                "reviewer": create_reviewer,
            }[role]
            agent = factory(model, instruction, schema)
            agent.model_settings = ModelSettings(max_tokens=self.settings.max_output_tokens)
            logger.info(
                "agent_start role=%s task=%s tools=%s max_turns=%s",
                role,
                task.task_id,
                [tool.name for tool in agent.tools],
                self.settings.agent_max_turns,
            )
            try:
                result = await Runner.run(
                    agent,
                    input=context,
                    context=self._evidence(task),
                    max_turns=self.settings.agent_max_turns,
                    # Keep proprietary source/outputs local; no OpenAI tracing export.
                    run_config=RunConfig(tracing_disabled=True, trace_include_sensitive_data=False),
                )
            except APIConnectionError as error:
                # The OpenAI client wraps exceptions from custom transports. Preserve
                # budget, truncation and local validation errors for workflow recovery.
                if isinstance(
                    error.__cause__, (ValueError, RuntimeError, OSError, httpx.HTTPError)
                ):
                    raise error.__cause__ from None
                raise ModelResponseError("Agent model connection failed") from None
            except MaxTurnsExceeded:
                raise ModelResponseError(
                    "Agent turn limit reached; no final artifact accepted"
                ) from None
            except ModelBehaviorError:
                # SDK errors may include rejected output text; keep it out of CLI logs.
                raise ModelResponseError("Agent returned an invalid structured artifact") from None
            logger.info(
                "agent_finish role=%s task=%s model_calls=%s",
                role,
                task.task_id,
                len(result.raw_responses),
            )
            return schema.model_validate(result.final_output)
