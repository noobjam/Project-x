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
    checkpoint_dsn: SecretStr | None = None
    max_revisions: int = Field(default=2, ge=0, le=5)
    max_output_tokens: int = Field(default=12_000, ge=256, le=64_000)
    max_input_characters: int = Field(default=2_000_000, ge=1_000, le=4_000_000)
    request_timeout_seconds: float = Field(default=120.0, gt=0, le=600)

    def require_llm(self) -> None:
        if not self.openrouter_api_key or not self.openrouter_api_key.get_secret_value().strip():
            raise ValueError("Set SOC_VERIFIER_OPENROUTER_API_KEY before calling a model")
        if not self.model.strip() or not self.provider.strip():
            raise ValueError("Set SOC_VERIFIER_MODEL and SOC_VERIFIER_PROVIDER explicitly")
