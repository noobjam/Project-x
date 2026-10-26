"""Environment-based configuration with redacted credentials."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SOC_VERIFIER_", env_file=".env", extra="ignore")

    openrouter_api_key: SecretStr | None = None
    model: str = ""
    provider: str = ""
    artifact_dir: Path = Path("artifacts")
    agent_max_turns: int = Field(default=4, ge=1, le=12)
    max_revisions: int = Field(default=2, ge=0, le=5)
    max_output_tokens: int = Field(default=12_000, ge=256, le=64_000)
    max_input_characters: int = Field(default=2_000_000, ge=1_000, le=4_000_000)
    request_timeout_seconds: float = Field(default=120.0, gt=0, le=600)
    chunk_max_characters: int = Field(default=24_000, ge=1000, le=100_000)
    plan_batch_size: int = Field(default=8, ge=1, le=32)
    batch_workers: int = Field(default=1, ge=1, le=8)
    max_model_calls: int = Field(default=200, ge=1, le=2000)
    max_cost_usd: float = Field(default=2.0, gt=0, le=1000)

    def require_agents(self) -> None:
        if not self.openrouter_api_key or not self.openrouter_api_key.get_secret_value().strip():
            raise ValueError("Set SOC_VERIFIER_OPENROUTER_API_KEY before calling a model")
        if not self.model.strip() or not self.provider.strip():
            raise ValueError("Set SOC_VERIFIER_MODEL and SOC_VERIFIER_PROVIDER explicitly")
