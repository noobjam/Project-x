"""Run actual SDK agents, with bounded tool loops and an OpenRouter model gateway."""

import asyncio
import logging
import re
from typing import Any

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
from soc_verifier.agents.base import AgentRole, ModelResponseError
from soc_verifier.agents.planner import create_planner
from soc_verifier.agents.reviewer import create_reviewer
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

    def _evidence(self) -> EvidenceContext:
        def latest(stem: str, initial: str | None = None) -> dict[str, Any] | None:
            names = sorted(
                path.name
                for path in self.artifacts.root.glob(f"{stem}.r*.json")
                if re.fullmatch(rf"{stem}\.r\d{{3}}\.json", path.name)
            )
            if names:
                return self.artifacts.read(names[-1])
            return (
                self.artifacts.read(initial) if initial and self.artifacts.exists(initial) else None
            )

        analysis, plan = latest("analysis", "analysis.json"), latest("plan")
        return EvidenceContext(
            Specification.model_validate(self.artifacts.read("specification.json")),
            SpecAnalysis.model_validate(analysis) if analysis is not None else None,
            VerificationPlan.model_validate(plan) if plan is not None else None,
        )

    def run[T: BaseModel](
        self, *, role: AgentRole, instruction: str, context: str, schema: type[T]
    ) -> T:
        return asyncio.run(
            self._run(role=role, instruction=instruction, context=context, schema=schema)
        )

    async def _run[T: BaseModel](
        self, *, role: AgentRole, instruction: str, context: str, schema: type[T]
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
                "agent_start role=%s tools=%s max_turns=%s",
                role,
                [tool.name for tool in agent.tools],
                self.settings.agent_max_turns,
            )
            try:
                result = await Runner.run(
                    agent,
                    input=context,
                    context=self._evidence(),
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
            logger.info("agent_finish role=%s model_calls=%s", role, len(result.raw_responses))
            return schema.model_validate(result.final_output)
