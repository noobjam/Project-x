# Contributing

Use the locked uv environment and quality commands in [README.md](README.md).
Keep source code under `src/`; tests import the installed package, not a modified
`PYTHONPATH`. Declare packages imported directly as direct dependencies.

Keep domain contracts independent of transport and orchestration. Put provider
details in `llm/`, external file formats in ingestion/export, and routing in a
workflow module. Add domain schema versions when changing persisted contracts;
do not silently reinterpret saved artifacts. Bump `PROMPT_VERSION` when changing
role behavior so a resumed run cannot silently mix prompt versions.

Add tests for behavior and failure boundaries: fabricated references, interrupted
runs, budget limits and adapter failures. Unit/integration tests must not access
live APIs or require proprietary specifications. Evaluation of engineering quality
is separate from the software test suite.

Never commit `.env`, credentials, specification documents, generated plans or
checkpoints. Do not log document text in operational logs. New LLM features should
preserve explicit model/endpoint selection and locally validate their outputs.

Update the smallest affected documentation when changing commands, settings or
workflow behavior. Future test-generation and EDA features should extend existing
contracts and artifact links without bypassing the planning workflow's evidence.
