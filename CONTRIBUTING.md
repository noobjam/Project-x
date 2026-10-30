# Contributing

Use the locked uv environment and quality commands in [README.md](README.md).
Keep source code under `src/`; tests import the installed package, not a modified
`PYTHONPATH`. Declare packages imported directly as direct dependencies.

Keep domain contracts independent of transport and orchestration. Put provider
details in `providers/`, SDK agent definitions and tools in `agents/`, external file formats in ingestion/export, and routing in a
workflow module. Add domain schema versions when changing persisted contracts;
do not silently reinterpret saved artifacts. Bump `PROMPT_VERSION` when changing
role behavior so a resumed run cannot silently mix prompt versions.

Add tests for behavior and failure boundaries: fabricated references, interrupted
runs, budget limits and adapter failures. Unit/integration tests must not access
live APIs or require proprietary specifications. Evaluation of engineering quality
is separate from the software test suite.

Never commit `.env`, credentials, specification documents, generated plans or
checkpoints. Do not log document text in operational logs. New agent features should
preserve explicit model/endpoint selection and locally validate their outputs.

Update the smallest affected documentation when changing commands, settings or
workflow behavior. Future test-generation and EDA features should extend existing
contracts and artifact links without bypassing the planning workflow's evidence.

Before pushing, run `python3 scripts/check_repository.py` after staging intended
files. It inspects the index only: local agent instructions, environment files
(except `.env.example`), Office documents, generated artifacts, private key files,
symlinks and common credential patterns are rejected without printing contents.
It is a backstop, not a complete detector of private prose. CI runs after upload;
keep GitHub secret push protection enabled and inspect staged files before pushing.

Main requires PRs, passing `repository-policy`, `quality (3.12)` and `quality (3.13)`
checks against the current base, and resolved review threads. Force pushes and
deletion are disabled, including administrator bypass. The repository currently
has one maintainer; required approval count stays zero until a separate reviewer
has access. Code review and explicit merge authorization still apply.

PR CI compares instruction syntax with the base and requires `PROMPT_VERSION` to
change with role instructions. Existing compatibility/resume/export tests remain
mandatory. A version bump alone does not establish correct behavior. Changes to
saved contracts require explicit compatibility evidence; agent behavior changes
must describe evaluation evidence or their untested, opt-in status in the PR.
Normal CI stays offline; paid model evaluation needs a declared approved budget.
