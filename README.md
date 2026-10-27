# SoC Verifier

An extensible Python application for agent-assisted, system-level ASIC verification.
The first workflow turns a specification into a source-linked draft verification plan.

The current slice includes DOCX ingestion, typed contracts, OpenAI Agents SDK
analyst/planner/reviewer agents, evidence retrieval tools, an OpenRouter gateway,
and Excel export. Python controls stage order, validation and durable artifacts;
the SDK runs each agent's model/tool loop. LangGraph is no longer a dependency.
Testbench generation, simulation, semantic retrieval and coverage closure are future work.

Offline baseline snapshots and the initial evaluation scope are documented in
[evals/README.md](evals/README.md). They preserve source/reference separation and
do not call a model. Current implementation status is in [docs/progress.md](docs/progress.md).

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync --locked
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
provider endpoint slug. Choose an endpoint supporting function tools, JSON Schema output and the
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
The planner works in requirement batches with a compact requirement directory as
context and retrieves additional requirements through tools. Review covers every source chunk plus a global integration pass.
Initial analysis remains `analysis.json`; revised analyses have
numbered filenames, and `result.json` identifies the final artifacts for export.
Transport, schema and traceability failures stop the run and preserve completed
work, including individual batch outputs. Resume retries unfinished work;
interrupted remote calls can have incurred charges. CLI runs reserve a conservative
maximum cost before every paid request, including tool follow-ups, using the pinned endpoint's advertised
context capacity and token prices. Reported charges settle those reservations;
unknown charges remain fully reserved, including after restart.
Only an explicitly identified OpenRouter in-flight
admission rejection is settled at zero because it never reaches inference. Pricing changes
on resume stop the run. This is a client-side safeguard, not an account-level
OpenRouter credit limit or protection against incorrect provider billing.

Controls in `.env.example` include chunk size, requirements per plan batch,
worker count, agent turn limit (default 4 per task), total attempted model calls
and dollar budget (default $2/run). SDK retries are disabled; failed calls consume
the same attempt budget. Tiered endpoint pricing currently fails preflight rather
than using an incomplete cost estimate.
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
A large run starts `2*C + B + 2` agent tasks before corrections,
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
start three agent tasks. Each task can make up to `AGENT_MAX_TURNS` model calls
while retrieving evidence. Tool access does not imply a cheaper run; measured
usage and engineering quality must be compared before changing defaults.

Global analysis/review receive section outlines and compact indexes, then retrieve
original evidence as needed. Local extraction and review still visit every source
chunk. Global quality now depends on the agent investigating relevant evidence;
it requires a fresh engineering evaluation. Oversized individual source blocks
fail explicitly rather than being truncated. Chunk sizes are character bounds,
not token-count guarantees; model output limits can still require smaller batches.
Tools return bounded results, and long source blocks support explicit pagination.

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
schema validation or completion checks fail. Local JSON artifacts do contain specification data. OpenAI trace export is disabled;
model requests go through OpenRouter using the existing key. Excel exports publish atomically,
refuse existing destinations, and leave no partial destination after a failed save.
Source references are validated for existence, not semantic correctness;
engineering review is still required.

## Repository layout

```text
src/soc_verifier/
  domain/                  # Provider/framework-independent artifact contracts
  ingestion/               # Deterministic source extraction
  agents/
    analyst.py             # SDK requirements analyst and its tools
    planner.py             # SDK verification planner and its tools
    reviewer.py            # SDK verification reviewer and its tools
    tools.py               # Search source, retrieve blocks/requirements/plan items
    runtime.py             # SDK Runner, bounded turns, local evidence context
    instructions.py        # Versioned agent instructions
    base.py                # Workflow-to-agent interface and errors
  providers/               # OpenRouter transport and shared spending ledger
  workflows/spec_to_plan/  # Batching, stage/revision policy, domain validation
  storage/                 # Immutable artifacts double as recovery checkpoints
  export/                  # Excel views of canonical artifacts
  settings.py              # Environment configuration, credentials redacted
  cli.py                   # Composition root and commands
tests/
  unit/                    # Contracts, ingestion, transport, storage, export
  integration/             # Real SDK/tool loops with a simulated OpenRouter API
docs/architecture.md       # Boundaries, decisions and extension points
.github/workflows/ci.yml   # Locked install, lint, types, tests, build
```

Completed batches and revisions are immutable recovery checkpoints. Resume replays
stage decisions, validates saved artifacts and executes only unfinished tasks.
An interrupted agent task restarts its tool conversation; earlier remote calls may
already have been charged and remain in the ledger. There is no exactly-once billing
guarantee. The application is a single process; multiple processes must not execute
the same run concurrently. SQLite/PostgreSQL graph checkpoint support and the
`postgres` extra have been removed.

## Reviewing the Agents SDK migration

The `migration/openai-agents-sdk` branch has been merged into `main`.
Commit `10f5bad` preserves the tested prototype; inspect the migration with
`git diff 10f5bad..5d15c10`. The merge includes the preserved prototype changes.

Prompt version 5 and engine `openai-agents-v1` identify new runs. Earlier runs
remain exportable and readable by `spend`, but cannot resume under this runtime.
Use the baseline checkout and its locked environment for an unfinished legacy run.
The four available tools are `search_spec`, `get_source_blocks`,
`get_requirements` and `get_plan_items`. They read only the current run's evidence.
The analyst has source tools; the planner additionally retrieves requirements;
the reviewer additionally retrieves full plan scenarios. `events.log` records
agent starts, tool names, model-call usage (including reported cache/reasoning
tokens) and completion. It does not log tool arguments or evidence text.

The OpenAI client SDK supplies API calls and the Agents SDK supplies the tool loop;
OpenRouter still supplies inference and billing. The model and provider remain
explicit configuration, shared across roles. Automatic model selection, per-role
model benchmarks, JEV and simulator tools are deferred. This migration has offline
SDK integration tests; it has not been validated on a new paid full-specification run.

The existing `.aura/` files are earlier planning notes. The current implementation
scope and commands are documented here and in [the architecture](docs/architecture.md).
The supplied proprietary DOCX/XLSX and generated artifacts are ignored by Git;
do not add them to fixtures or CI. The reference VPlan is evaluation material and
is not given to the generation workflow.
