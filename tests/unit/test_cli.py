from uuid import uuid4

from docx import Document
from typer.testing import CliRunner

from soc_verifier.cli import app
from soc_verifier.domain.models import Specification
from soc_verifier.settings import Settings
from soc_verifier.storage.artifacts import ArtifactStore

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output and "resume" in result.output


def test_cli_local_ingest(tmp_path):
    source = tmp_path / "source.docx"
    output = tmp_path / "specification.json"
    doc = Document()
    doc.add_paragraph("System reset clears pending interrupts.")
    doc.save(source)
    result = runner.invoke(app, ["ingest", str(source), "--output", str(output)])
    assert result.exit_code == 0, result.output
    assert len(Specification.model_validate_json(output.read_text()).blocks) == 1


def test_resume_rejects_path_traversal():
    result = runner.invoke(app, ["resume", "../../etc"])
    assert result.exit_code == 1


def test_spend_works_without_credentials_and_watch_stops_at_completion(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, artifact_dir=tmp_path, openrouter_api_key=None)
    monkeypatch.setattr("soc_verifier.cli.Settings", lambda: settings)
    run_id = str(uuid4())
    artifacts = ArtifactStore(tmp_path / "runs" / run_id)
    artifacts.write(
        "manifest.json", {"model": "test/model", "max_cost_usd": 2, "max_model_calls": 10}
    )
    artifacts.write("cost-reserved.00001.json", {"attempt": 1, "reserved_usd": "0.4"})
    artifacts.write("cost-settled.00001.json", {"attempt": 1, "cost_usd": "0.1"})
    artifacts.write("cost-reserved.00002.json", {"attempt": 2, "reserved_usd": "0.4"})
    sleeps = []

    def finish(seconds):
        sleeps.append(seconds)
        artifacts.write("result.json", {"status": "needs_review"})

    monkeypatch.setattr("soc_verifier.cli.sleep", finish)
    result = runner.invoke(app, ["spend", run_id, "--watch"])
    assert result.exit_code == 0, result.output
    assert "Reported $0.100000" in result.output
    assert "Reserved $0.400000 (1 unsettled)" in result.output
    assert "Budget available $1.500000" in result.output
    assert "Attempts 2/10" in result.output
    assert "Run completed: needs_review" in result.output
    assert sleeps == [5]


def test_spend_unknown_run_does_not_create_directories(tmp_path, monkeypatch):
    settings = Settings(_env_file=None, artifact_dir=tmp_path / "absent")
    monkeypatch.setattr("soc_verifier.cli.Settings", lambda: settings)
    result = runner.invoke(app, ["spend", str(uuid4())])
    assert result.exit_code == 1
    assert "Unknown run ID" in result.output
    assert not settings.artifact_dir.exists()
