from unittest.mock import Mock

import pytest
from pydantic import SecretStr
from typer.testing import CliRunner

from soc_verifier.cli import app
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore

pytestmark = pytest.mark.integration
runner = CliRunner()


def test_cli_plan_resume_and_export(
    tmp_path, monkeypatch, specification, analysis, verification_plan, clean_review
):
    settings = Settings(
        _env_file=None,
        artifact_dir=tmp_path / "artifacts",
        openrouter_api_key=SecretStr("test-only"),
        model="test/model",
        provider="test-endpoint",
        checkpoint_dsn=None,
    )
    monkeypatch.setattr("soc_verifier.cli.Settings", lambda: settings)
    llm = Mock()
    llm.generate.side_effect = [analysis, verification_plan, clean_review]
    monkeypatch.setattr("soc_verifier.cli.OpenRouterLLM", lambda settings, client: llm)
    source = ArtifactStore(tmp_path).write("specification.json", specification)

    generated = runner.invoke(app, ["plan", str(source)])
    assert generated.exit_code == 0, generated.output
    runs = list((settings.artifact_dir / "runs").iterdir())
    assert len(runs) == 1
    run_id = runs[0].name
    assert ArtifactStore(runs[0]).read("result.json")["status"] == "draft_ready"

    resumed = runner.invoke(app, ["resume", run_id])
    assert resumed.exit_code == 0, resumed.output
    assert "already completed" in resumed.output
    assert llm.generate.call_count == 3

    exported = runner.invoke(app, ["export", run_id, "-o", str(tmp_path / "plan.xlsx")])
    assert exported.exit_code == 0, exported.output
    assert (tmp_path / "plan.xlsx").is_file()

    changed = settings.model_copy(update={"model": "different/model"})
    monkeypatch.setattr("soc_verifier.cli.Settings", lambda: changed)
    rejected = runner.invoke(app, ["resume", run_id])
    assert rejected.exit_code == 1
    assert "configuration changed" in rejected.output
    assert llm.generate.call_count == 3


def test_cli_requires_explicit_credentials(tmp_path, monkeypatch, specification):
    settings = Settings(
        _env_file=None,
        artifact_dir=tmp_path / "artifacts",
        openrouter_api_key=None,
    )
    monkeypatch.setattr("soc_verifier.cli.Settings", lambda: settings)
    source = ArtifactStore(tmp_path).write("specification.json", specification)
    result = runner.invoke(app, ["plan", str(source)])
    assert result.exit_code == 1
    assert "SOC_VERIFIER_OPENROUTER_API_KEY" in result.output
    assert not settings.artifact_dir.exists()
