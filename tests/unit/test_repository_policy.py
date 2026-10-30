import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/check_repository.py"
PROMPTS = "src/soc_verifier/agents/instructions.py"


@pytest.fixture
def repository(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "config", "user.name", "Policy test"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True
    )
    return tmp_path


def stage(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    subprocess.run(["git", "add", "--", name], cwd=root, check=True)


def run(root, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=root, text=True, capture_output=True
    )


@pytest.mark.parametrize(
    "name",
    [
        "AGENTS.md",
        "nested/Agents.MD",
        ".env.local",
        "artifacts/out.json",
        "input.docx",
        "plan.xlsx",
    ],
)
def test_private_files_are_rejected(repository, name):
    stage(repository, name, "private text")
    result = run(repository)
    assert result.returncode == 1 and name in result.stdout
    assert "private text" not in result.stdout


def test_untracked_working_files_are_never_read(repository):
    stage(repository, ".env.example", "OPENROUTER_API_KEY=\n")
    (repository / ".env").write_text("untracked secret")
    (repository / "AGENTS.md").write_text("local instructions")
    assert run(repository).returncode == 0


def test_credential_is_redacted(repository):
    secret = "sk-or-" + "v1-" + "a" * 64
    stage(repository, "settings.txt", secret)
    result = run(repository)
    assert result.returncode == 1 and "credential" in result.stdout
    assert secret not in result.stdout + result.stderr


def test_symlink_cannot_expose_local_file(repository, tmp_path_factory):
    outside = tmp_path_factory.mktemp("private") / "source"
    outside.write_text("private secret text")
    (repository / "link").symlink_to(outside)
    subprocess.run(["git", "add", "link"], cwd=repository, check=True)
    result = run(repository)
    assert result.returncode == 1 and "symlink" in result.stdout
    assert outside.read_text() not in result.stdout


@pytest.mark.parametrize(
    "change,version,expected", [("new", "1", 1), ("new", "2", 0), ("old", "1", 0)]
)
def test_prompt_change_requires_version(repository, change, version, expected):
    stage(repository, PROMPTS, 'PROMPT_VERSION = "1"\nANALYZE = "old"\n')
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=repository, check=True)
    stage(repository, PROMPTS, f'PROMPT_VERSION = "{version}"\nANALYZE = "{change}"\n# Comment\n')
    assert run(repository, "--base", "HEAD").returncode == expected


def test_missing_base_fails_closed(repository):
    stage(repository, PROMPTS, 'PROMPT_VERSION = "1"\nANALYZE = "old"\n')
    assert run(repository, "--base", "nonexistent").returncode == 1
