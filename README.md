# SoC Verifier

An extensible Python application for agent-assisted, system-level ASIC verification.
The first workflow turns a specification into a source-linked draft verification plan.

The current slice includes DOCX ingestion, typed contracts, an OpenRouter adapter,
a persistent LangGraph analysis/planning/review loop, and Excel export. Testbench
generation, simulation, semantic retrieval and coverage closure are future work.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync --locked --all-extras
uv run soc-verifier --help
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=soc_verifier
uv build
```

Python 3.12 is the development baseline. `uv.lock` fixes dependency versions. Use
`uv add` for dependency changes and review the lockfile diff. Tests never call a
paid model and do not need credentials or the proprietary example documents.

## Local extraction

```bash
uv run soc-verifier ingest Management_CPU_ss_spec.docx --output artifacts/specification.json
```

Extraction is local and preserves ordered paragraphs/table rows with XML locators
and a document hash. It reports unprocessed media, comments and other unsupported
content instead of claiming complete interpretation. Visual interpretation and
layout-aware table normalization remain future work.

## Generate a plan

Copy `.env.example` to `.env` and set the API key, explicit OpenRouter model ID and
provider endpoint slug. Choose an endpoint supporting JSON Schema output and the
configured data-handling requirements. Planning sends extracted content to
OpenRouter and the selected inference provider and incurs usage charges.

```bash
uv run soc-verifier plan artifacts/specification.json
uv run soc-verifier resume <run-id>
uv run soc-verifier export <run-id> --output artifacts/verification_plan.xlsx
```

Every run gets its own directory under `artifacts/runs/`. JSON artifacts are
immutable and authoritative; Excel is a review view. Exports refuse existing
targets. A clean automated review produces `draft_ready`, never human approval
or a claim that hardware has been verified. Findings, source gaps, extraction
warnings or open questions produce `needs_review`.

Only errors from plan review trigger revisions. The maximum is two by default:
at most seven model calls in a normally completed run. Transport, schema and
traceability failures stop the run and preserve completed work. Resume retries
unfinished work; interrupted remote calls can have incurred charges. The current
limits bound revisions, input characters and output tokens, not an exact dollar
amount. Whole-document context is bounded; automatic chunking is not implemented.
The supplied specification extracts to about 1.3 MB of JSON. Select a model with
sufficient context capacity; the character guard is not a token-count guarantee.

OpenRouter routing is explicit, provider fallbacks are disabled, and data
collection is denied with ZDR required. These controls can leave no eligible
endpoint. Logs contain request metadata, not prompt/completion text. Local JSON
and checkpoints do contain specification data. Source references are validated
for existence, not semantic correctness; engineering review is still required.

## Repository layout

```text
src/soc_verifier/
  domain/                  # Provider/framework-independent artifact contracts
  ingestion/               # Deterministic source extraction
  llm/                     # StructuredLLM protocol and OpenRouter transport
  workflows/spec_to_plan/  # LangGraph state, nodes, routing and role instructions
  storage/                 # Immutable artifacts and persistent checkpoints
  export/                  # Excel views of canonical artifacts
  settings.py              # Environment configuration, credentials redacted
  cli.py                   # Composition root and commands
tests/
  unit/                    # Contracts, ingestion, transport, storage, export
  integration/             # Real graph execution with fake LLM responses
docs/architecture.md       # Boundaries, decisions and extension points
.github/workflows/ci.yml   # Locked install, lint, types, tests, build
```

SQLite is the default checkpoint backend for local development. Install the
`postgres` extra and set `SOC_VERIFIER_CHECKPOINT_DSN` to use PostgreSQL checkpoints.
Domain artifacts remain local JSON in both modes. The application is a single
process; multiple processes must not execute the same run concurrently.

The existing `.aura/` files are earlier planning notes. The current implementation
scope and commands are documented here and in [the architecture](docs/architecture.md).
The supplied proprietary DOCX/XLSX and generated artifacts are ignored by Git;
do not add them to fixtures or CI. The reference VPlan is evaluation material and
is not given to the generation workflow.
