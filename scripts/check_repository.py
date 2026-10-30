"""Offline checks of the Git index; never read ignored files or follow symlinks."""

import argparse
import ast
import re
import subprocess
from pathlib import PurePosixPath

PROMPTS = "src/soc_verifier/agents/instructions.py"
SECRETS = re.compile(
    rb"sk-or-v1-[a-fA-F0-9]{40,}|sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}"
    rb"|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}"
    rb"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
)


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], stderr=subprocess.PIPE)


def forbidden(path: str) -> bool:
    item = PurePosixPath(path.lower())
    return (
        item.name == "agents.md"
        or (item.name.startswith(".env") and item.name != ".env.example")
        or "artifacts" in item.parts
        or item.suffix in {".docx", ".xlsx", ".xls", ".sqlite", ".sqlite3", ".pem", ".key"}
    )


def prompt_signature(content: bytes) -> tuple[str, str]:
    tree = ast.parse(content)
    versions = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "PROMPT_VERSION" for t in node.targets)
    ]
    if len(versions) != 1:
        raise ValueError("Expected one literal PROMPT_VERSION")
    version = ast.literal_eval(versions[0].value)
    if not isinstance(version, str) or not version:
        raise ValueError("PROMPT_VERSION must be a nonempty string")
    tree.body = [
        node
        for node in tree.body
        if node not in versions
        and not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
    ]
    return version, ast.dump(tree, include_attributes=False)


def check(base: str | None) -> list[str]:
    errors = []
    files = {}
    for row in git("ls-files", "--stage", "-z").split(b"\0"):
        if not row:
            continue
        meta, name = row.split(b"\t", 1)
        mode, _oid, stage = meta.split()
        path = name.decode("utf-8")
        if stage != b"0" or mode not in {b"100644", b"100755"}:
            errors.append(f"{path}: unresolved entry, symlink or submodule is not allowed")
            continue
        if forbidden(path):
            errors.append(f"{path}: local/private artifact must not be tracked")
            continue
        content = git("show", f":{path}")
        files[path] = content
        if SECRETS.search(content):
            errors.append(f"{path}: possible credential; content is redacted")
    if base and PROMPTS in files:
        git("rev-parse", "--verify", f"{base}^{{commit}}")
        if git("ls-tree", "-r", "--name-only", base, "--", PROMPTS).splitlines():
            old_version, old_prompt = prompt_signature(git("show", f"{base}:{PROMPTS}"))
            new_version, new_prompt = prompt_signature(files[PROMPTS])
            if new_prompt != old_prompt and new_version == old_version:
                errors.append(f"{PROMPTS}: changed instructions require a new PROMPT_VERSION")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="PR base commit for prompt-version comparison")
    args = parser.parse_args()
    try:
        errors = check(args.base)
    except (OSError, ValueError, SyntaxError, subprocess.CalledProcessError):
        print("Repository policy could not validate its inputs; no file contents printed.")
        return 1
    for error in errors:
        print(error)
    if not errors:
        print("Repository policy passed (indexed files only; no model calls).")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
