from docx import Document
from typer.testing import CliRunner

from soc_verifier.cli import app
from soc_verifier.domain.models import Specification

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
