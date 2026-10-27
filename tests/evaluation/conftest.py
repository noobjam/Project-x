import subprocess

import pytest


@pytest.fixture
def evaluation_repo(tmp_path, monkeypatch):
    root = tmp_path / "repository"
    root.mkdir()
    (root / ".gitignore").write_text("artifacts/\n")
    (root / "uv.lock").write_text("version = 1\n")
    for args in [
        ["init", "-q"],
        ["add", ".gitignore", "uv.lock"],
        [
            "-c",
            "user.name=Synthetic Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "Fixture",
        ],
    ]:
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    monkeypatch.chdir(root)
    return root
