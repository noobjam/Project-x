"""Run actual SDK agents, with bounded tool loops and an OpenRouter model gateway."""

import asyncio
import json
import logging
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx
from agents import (
    MaxTurnsExceeded,
    ModelBehaviorError,
    ModelSettings,
    OpenAIChatCompletionsModel,
    OpenAIResponsesModel,
    RunConfig,
    Runner,
    UserError,
)
from openai import APIConnectionError, AsyncOpenAI
from openai.types.shared import Reasoning
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
from soc_verifier.agents.testbench import create_testbench
from soc_verifier.agents.tools import EvidenceContext, get_knowledge_entries, search_knowledge
from soc_verifier.domain.hardware import HardwareSnapshot
from soc_verifier.domain.knowledge import KnowledgeSnapshot
from soc_verifier.domain.models import SpecAnalysis, Specification, VerificationPlan
from soc_verifier.domain.readiness import GapAssessment, GapEvidence
from soc_verifier.domain.testbench import directed_execution_profile
from soc_verifier.domain.testbench_proposal import (
    ExperimentalTestbenchProposal,
    ObservedTestbenchProposal,
    TestbenchProposal,
)
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
        self._check_planner_turn_capacity(self.artifacts.exists("knowledge.json"))
        configuration = self.settings.agent_configuration()
        if self.artifacts.exists("knowledge.json"):
            configuration["knowledge"] = ArtifactReference.capture(
                self.artifacts, "knowledge.json"
            ).model_dump()
            configuration["knowledge_consultation"] = "required-search-read-v1"
        return configuration

    def _check_planner_turn_capacity(self, has_knowledge: bool) -> None:
        if self.settings.planner_source_lookup and self.settings.agent_max_turns < (
            5 if has_knowledge else 3
        ):
            raise ValueError(
                "Planner turn limit must allow source/knowledge search, read and final output"
            )

    def _evidence(
        self,
        task: TaskEnvelope,
        accesses: list[dict[str, Any]],
        source_accesses: list[dict[str, Any]],
        hardware_accesses: list[dict[str, Any]],
    ) -> EvidenceContext:
        references = task.inputs.evidence
        source = references["source"].read(self.artifacts)
        analysis = references["analysis"].read(self.artifacts) if "analysis" in references else None
        plan = references["plan"].read(self.artifacts) if "plan" in references else None
        for evidence_reference in references.values():
            evidence_reference.read(self.artifacts)
        reference = references.get("knowledge")
        actual = (
            ArtifactReference.capture(self.artifacts, "knowledge.json")
            if self.artifacts.exists("knowledge.json")
            else None
        )
        if reference != actual:
            raise ValueError("Task knowledge binding does not match the run snapshot")
        knowledge = (
            KnowledgeSnapshot.model_validate(reference.read(self.artifacts)) if reference else None
        )
        hardware_reference = references.get("hardware")
        actual_hardware = (
            ArtifactReference.capture(self.artifacts, "hardware.json")
            if self.artifacts.exists("hardware.json")
            else None
        )
        if hardware_reference != actual_hardware:
            raise ValueError("Task hardware binding does not match the run snapshot")
        hardware = (
            HardwareSnapshot.model_validate(hardware_reference.read(self.artifacts))
            if hardware_reference
            else None
        )

        def audit_hardware(record: dict[str, Any]) -> None:
            invocation = current_invocation.get()
            if invocation is None or hardware_reference is None:
                raise ValueError("RTL access requires a bound hardware invocation")
            self.artifacts.write(
                f"hardware-access.{uuid4()}.json",
                {
                    "format": "hardware-access-v1",
                    **invocation.attribution(),
                    "snapshot_sha256": hardware_reference.sha256,
                    **record,
                },
            )
            hardware_accesses.append(record)

        def audit(record: dict[str, Any]) -> None:
            invocation = current_invocation.get()
            if invocation is None or reference is None:
                raise ValueError("Knowledge access requires a bound invocation")
            self.artifacts.write(
                f"knowledge-access.{uuid4()}.json",
                {
                    "format": "knowledge-access-v1",
                    "created_at": datetime.now(UTC).isoformat(),
                    **invocation.attribution(),
                    "role": task.inputs.role,
                    "snapshot_sha256": reference.sha256,
                    **record,
                },
            )
            accesses.append(record)

        def audit_source(record: dict[str, Any]) -> None:
            invocation = current_invocation.get()
            if invocation is None:
                raise ValueError("Source access requires a bound invocation")
            self.artifacts.write(
                f"source-access.{uuid4()}.json",
                {
                    "format": "source-access-v1",
                    "created_at": datetime.now(UTC).isoformat(),
                    **invocation.attribution(),
                    "snapshot_sha256": references["source"].sha256,
                    **record,
                },
            )
            source_accesses.append(record)

        return EvidenceContext(
            Specification.model_validate(source),
            SpecAnalysis.model_validate(analysis) if analysis is not None else None,
            VerificationPlan.model_validate(plan) if plan is not None else None,
            knowledge,
            audit if knowledge else None,
            audit_source,
            hardware,
            audit_hardware if hardware else None,
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
                        "source": ArtifactReference.capture(self.artifacts, "specification.json"),
                        **(
                            {
                                "knowledge": ArtifactReference.capture(
                                    self.artifacts, "knowledge.json"
                                )
                            }
                            if self.artifacts.exists("knowledge.json")
                            else {}
                        ),
                        **(
                            {"hardware": ArtifactReference.capture(self.artifacts, "hardware.json")}
                            if self.artifacts.exists("hardware.json")
                            else {}
                        ),
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
            responses_api = self.settings.model_api == "responses"
            model = (
                OpenAIResponsesModel(model=self.settings.model, openai_client=client)
                if responses_api
                else OpenAIChatCompletionsModel(model=self.settings.model, openai_client=client)
            )
            factory = {
                "analyst": create_analyst,
                "planner": create_planner,
                "reviewer": create_reviewer,
                "testbench": create_testbench,
            }[role]
            agent = factory(model, instruction, schema)
            agent.model_settings = ModelSettings(max_tokens=self.settings.max_output_tokens)
            if responses_api:
                agent.model_settings.store = False
                agent.model_settings.truncation = "disabled"
                agent.model_settings.response_include = ["reasoning.encrypted_content"]
                effort = self.settings.reasoning_effort
                if effort is None and self.settings.model == "openai/gpt-6.1-terra":
                    effort = "medium"
                if effort is not None:
                    agent.model_settings.reasoning = Reasoning(effort=effort)
            accesses: list[dict[str, Any]] = []
            source_accesses: list[dict[str, Any]] = []
            hardware_accesses: list[dict[str, Any]] = []
            evidence = self._evidence(task, accesses, source_accesses, hardware_accesses)
            require_hardware = role == "testbench"
            require_gap_scope = role == "reviewer" and task.inputs.stage == "execution.gaps"
            if require_gap_scope and (
                evidence.analysis is None
                or evidence.hardware is None
                or self.settings.agent_max_turns < (5 if evidence.knowledge else 3)
            ):
                raise ValueError(
                    "Gap assessment needs bound analysis, hardware and source-read turns"
                )
            if require_hardware and (
                evidence.hardware is None
                or evidence.analysis is None
                or evidence.plan is None
                or self.settings.agent_max_turns < (6 if evidence.knowledge else 4)
            ):
                raise ValueError(
                    "Testbench agent needs bound hardware, analysis, plan and read turns"
                )
            if evidence.hardware is not None:
                context += "\nDeclared hardware configuration (not a behavioral specification):\n"
                context += json.dumps(
                    {
                        "hardware_target": evidence.hardware.target.model_dump(),
                        "execution_profile": directed_execution_profile(
                            evidence.hardware.target.probes
                        ),
                        "rtl_sources": [
                            {"id": s.id, "sha256": s.sha256, "lines": len(s.text.splitlines())}
                            for s in evidence.hardware.sources
                        ],
                        "instruction": "Expected behavior comes from the spec; report conflicts.",
                    }
                )
            require_source = (
                require_hardware
                or require_gap_scope
                or (role == "planner" and self.settings.planner_source_lookup)
            )
            if require_source:
                self._check_planner_turn_capacity(evidence.knowledge is not None)
            if evidence.knowledge is not None:
                agent.tools.extend([search_knowledge, get_knowledge_entries])

            def next_tool() -> str:
                for required, records, search, read, id_key in (
                    (
                        evidence.knowledge is not None,
                        accesses,
                        "search_knowledge",
                        "get_knowledge_entries",
                        "entry_ids",
                    ),
                    (
                        require_source,
                        source_accesses,
                        "search_spec",
                        "get_source_blocks",
                        "source_ids",
                    ),
                ):
                    if not required:
                        continue
                    searches = [r for r in records if r["tool"] == search]
                    if not searches:
                        return search
                    matches = {identifier for r in searches for identifier in r[id_key]}
                    reads = {
                        identifier for r in records if r["tool"] == read for identifier in r[id_key]
                    }
                    if matches and not matches.intersection(reads):
                        return read
                return "read_rtl" if require_hardware and not hardware_accesses else "auto"

            if evidence.knowledge is not None or require_source or require_hardware:
                # Enforce actual search/read turns; relevance and adequacy still need review.
                agent.reset_tool_choice = False
                agent.model_settings.tool_choice = next_tool()
                persist_knowledge = evidence.knowledge_audit
                persist_source = evidence.source_audit
                persist_hardware = evidence.hardware_audit

                def audit_knowledge_and_route(record: dict[str, Any]) -> None:
                    assert persist_knowledge is not None
                    persist_knowledge(record)
                    agent.model_settings.tool_choice = next_tool()

                def audit_source_and_route(record: dict[str, Any]) -> None:
                    assert persist_source is not None
                    persist_source(record)
                    agent.model_settings.tool_choice = next_tool()

                def audit_hardware_and_route(record: dict[str, Any]) -> None:
                    assert persist_hardware is not None
                    persist_hardware(record)
                    agent.model_settings.tool_choice = next_tool()

                evidence = replace(
                    evidence,
                    knowledge_audit=audit_knowledge_and_route if evidence.knowledge else None,
                    source_audit=audit_source_and_route,
                    hardware_audit=audit_hardware_and_route if evidence.hardware else None,
                )
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
                    context=evidence,
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
            except (ModelBehaviorError, UserError):
                # SDK errors may include rejected output text; keep it out of CLI logs.
                raise ModelResponseError("Agent returned an invalid structured artifact") from None
            if next_tool() != "auto":
                raise ModelResponseError(
                    "Agent completed without consulting required source or knowledge evidence"
                )
            logger.info(
                "agent_finish role=%s task=%s model_calls=%s",
                role,
                task.task_id,
                len(result.raw_responses),
            )
            value = schema.model_validate(result.final_output)
            quotes: list[GapEvidence] = []
            if require_gap_scope:
                if not isinstance(value, GapAssessment):
                    raise ModelResponseError("Gap assessment returned the wrong contract")
                quotes = [quote for gap in value.gaps for quote in gap.evidence]
            if isinstance(value, ExperimentalTestbenchProposal):
                quotes = [quote for issue in value.issue_assessments for quote in issue.evidence]
            if quotes:
                blocks = {b.id: b.text for b in evidence.specification.blocks}
                read_spans = [
                    span
                    for record in source_accesses
                    if record["tool"] == "get_source_blocks"
                    for span in record["spans"]
                ]
                if any(
                    not any(
                        quote.source_id == span["id"]
                        and quote.quote
                        in blocks[span["id"]][span["start_character"] : span["end_character"]]
                        for span in read_spans
                    )
                    for quote in quotes
                ):
                    raise ModelResponseError(
                        "Execution assessment must quote specification text actually read"
                    )
            if require_hardware and (
                not isinstance(
                    value,
                    (TestbenchProposal, ObservedTestbenchProposal, ExperimentalTestbenchProposal),
                )
                or set(value.rtl_source_ids)
                - {
                    identifier
                    for record in hardware_accesses
                    for identifier in record["source_ids"]
                }
            ):
                raise ModelResponseError("Testbench proposal must cite RTL actually read")
            if isinstance(
                value, (TestbenchProposal, ObservedTestbenchProposal, ExperimentalTestbenchProposal)
            ):
                read_ids = {
                    identifier
                    for record in source_accesses
                    if record["tool"] == "get_source_blocks"
                    for identifier in record["source_ids"]
                }
                if any(
                    set(check.source_ids) - read_ids
                    for step in value.steps
                    for check in step.checks
                ):
                    raise ModelResponseError("Testbench checks must cite specification blocks read")
            return value
