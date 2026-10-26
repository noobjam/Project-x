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

Extraction is local and preserves ordered paragraphs/table rows, body content
controls, tabs and line breaks with XML locators and a document hash. It reports
unprocessed media, comments and other unsupported content instead of claiming
complete interpretation. Visual interpretation and
layout-aware table normalization remain future work.

## Generate a plan

Copy `.env.example` to `.env` and set the API key, explicit OpenRouter model ID and
provider endpoint slug. Choose an endpoint supporting JSON Schema output and the
configured data-handling requirements. Planning sends extracted content to
OpenRouter and the selected inference provider and incurs usage charges.

```bash
uv run soc-verifier plan artifacts/specification.json
uv run soc-verifier resume <run-id>
uv run soc-verifier resume <run-id> --workers 1  # Resume sequentially
uv run soc-verifier resume <run-id> --workers 1 --max-output-tokens 6000
uv run soc-verifier export <run-id> --output artifacts/verification_plan.xlsx
```

Monitor a run from another terminal with `uv run soc-verifier spend <run-id> --watch`.
It refreshes every five seconds and stops when the run completes; Ctrl-C stops
only the monitor. Omit `--watch` for a single snapshot. This command is local and
does not require an API key or make paid requests. It separates provider-reported
charges from outstanding reservations for in-flight or unknown charges, and shows
the remaining run budget and attempted-call count. Available budget must cover the
next full reservation before another request can start. An interrupted run's
monitor keeps watching until stopped. Older runs without a ledger require their
`events.log` instead. Account-wide spending and per-key filters are available in
[OpenRouter Activity](https://openrouter.ai/activity); an API key's spending cap is
separate from the account's credit balance and this application's per-run cap.

Every run gets its own directory under `artifacts/runs/`. JSON artifacts are
immutable and authoritative; Excel is a review view. Exports refuse existing
targets. A clean automated review produces `draft_ready`, never human approval
or a claim that hardware has been verified. Findings, source gaps, extraction
warnings or open questions produce `needs_review`.

Review findings target `analysis`, `plan`, or `specification`. Repairable errors
return to the analyst or planner; source ambiguities remain visible for human
resolution without futile retries. The shared revision maximum is two by default.
Large specifications are partitioned into bounded source chunks; the analyst
extracts each chunk, Python merges exact duplicate statements without dropping
distinct requirements, and a global analyst pass adds cross-component requirements.
The planner works in requirement batches with the global requirement index as
context. Review covers every source chunk plus a global integration pass.
Initial analysis remains `analysis.json`; revised analyses have
numbered filenames, and `result.json` identifies the final artifacts for export.
Transport, schema and traceability failures stop the run and preserve completed
work, including individual batch outputs. Resume retries unfinished work;
interrupted remote calls can have incurred charges. CLI runs reserve a conservative
maximum cost before each paid request using the pinned endpoint's advertised
context capacity and token prices. Reported charges settle those reservations;
unknown charges remain fully reserved, including after restart.
Only an explicitly identified OpenRouter in-flight
admission rejection is settled at zero because it never reaches inference. Pricing changes
on resume stop the run. This is a client-side safeguard, not an account-level
OpenRouter credit limit or protection against incorrect provider billing.

Controls in `.env.example` include chunk size, requirements per plan batch,
worker count, total attempted model calls and dollar budget (default $2/run).
One batch is executed at a time by default; increase `BATCH_WORKERS` explicitly
for bounded concurrency. `resume --workers 1` overrides scheduling for that
execution without changing the saved manifest, prompts, or budget.
Use a lower `--max-output-tokens` ceiling on resume when a request's token allowance
exceeds available provider credit.
That override may only decrease the original limit, is logged for the execution,
and retains the original conservative cost reservation. Existing artifacts are
reused; no evidence is truncated. Lower output ceilings can cause more adaptive
splits and calls. HTTP failures
record the provider's error message and allowlisted reason metadata in
`http-error.<attempt>.json` and `events.log`, with credentials and full input
strings redacted; raw upstream error payloads are excluded.
Completed model response text is saved separately as `model-output.<attempt>.json`
for diagnosing rejected candidates. These files contain sensitive source-derived
content and are never treated as validated analysis, plan, or review artifacts.
A large run uses `2*C + B + 2` calls before corrections,
where C is source chunks and B is planning batches. Output-truncated batches
are bisected into smaller tasks; split decisions and completed children are
persisted, so resume does not repeat a known oversized parent. These extra calls
also consume the shared budgets. Invalid chunk source citations get one explicit
correction request using the same evidence and validation feedback; unsupported
claims must be removed, not assigned invented references. A second invalid result
stops. Invalid review item IDs also get one correction with the original evidence
and rejected review; findings without an associated plan item must use an empty
ID list. A second invalid review stops without publishing it as a valid artifact.
Citation corrections consume the same cost/call budgets and are logged.
Planning batches with missing or unknown requirement references similarly receive
one validation-feedback correction using the existing planner instructions and
original assigned requirements. A second invalid plan stops; previously validated
batches remain reusable. This repair also consumes the shared call/cost budgets.
Single-item overflow, schema errors, refusals
and transport failures stop rather than retrying indefinitely. Small inputs
retain the three-call path. Failed calls consume the attempt budget too.

Global analysis/review still need the full source and compact indexes to fit the
model context and input-character guard. Oversized individual source blocks fail
explicitly rather than being truncated. Chunk sizes are character bounds, not
token-count guarantees; model output limits can still require smaller batches.

The first full-text trial on the supplied SPEC reached the 64,000-token output
limit during requirement extraction (Gemini 2.5 Flash-Lite). The incomplete
response was rejected. The chunked workflow addresses that unbounded-output
design; a large input context window alone does not solve it. Model/planning
quality still requires comparison against the human reference, not just a
successful run or complete syntactic traceability.

OpenRouter routing is explicit, provider fallbacks are disabled, and data
collection is denied with ZDR required. These controls can leave no eligible
endpoint. Schema constants are normalized to singleton enums for endpoint
compatibility, and local validation remains mandatory. Logs contain request
metadata, not prompt/completion text; response usage is recorded even when local
schema validation or completion checks fail. Local JSON and checkpoints do contain
specification data. Excel exports publish atomically,
refuse existing destinations, and leave no partial destination after a failed save.
Source references are validated for existence, not semantic correctness;
engineering review is still required.

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
