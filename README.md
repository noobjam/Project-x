# SoC Verifier

An extensible Python application for agent-assisted, system-level ASIC verification.
The product sequence is specification -> verification plan -> testbench -> simulation
-> coverage improvement. The first implemented workflow produces a source-linked
draft verification plan; engineering review is a checkpoint in that pipeline.

The current slice includes DOCX ingestion, typed contracts, OpenAI Agents SDK
analyst/planner/reviewer agents, evidence retrieval tools, an OpenRouter gateway,
and Excel export. Python controls stage order, validation and durable artifacts;
the SDK runs each agent's model/tool loop. LangGraph is no longer a dependency.
An opt-in connected workflow passes the actual plan to a testbench agent, validates
its proposed checks, generates a directed testbench and runs simulation. The separate
authored-binding commands remain available. Broader environments, semantic retrieval
and coverage closure remain future work; live quality needs separate validation.

Offline snapshots, source packets and evaluation scoring are documented in
[evals/README.md](evals/README.md). They preserve source/reference separation and
do not call a model. The separate [source-audit calibration runner](evals/source-audit-protocol.md)
has an explicitly paid execution command with a shared budget across frozen cases.
Current implementation status is in [docs/progress.md](docs/progress.md).

Engineers can review proposed knowledge entries, source evidence and testbench
subchecklists in the [knowledge curation pack](docs/knowledge/README.md). These
documents remain unapproved. Agents can consult them only when an explicit
knowledge catalog is selected; provisional entries also require a trial opt-in.

## Connected verification workflow

`verify` accepts a DOCX or extracted specification JSON, declared hardware target
and standalone RTL files. It runs the analyst, planner and reviewer, then sends
each simulation plan item to the testbench agent. The agent reads specification,
RTL and any enabled KB, and proposes input sequences and expected output values.
Python validates the proposal, generates SystemVerilog, compiles and runs it.
There is no authored analysis, plan or test-sequence input to this command.

```bash
SOC_VERIFIER_AGENT_MAX_TURNS=8 uv run soc-verifier verify artifacts/specification.json \
  --hardware artifacts/hardware-target.json --rtl path/to/design.sv \
  --max-cost-usd 1 --max-model-calls 40
```

The `hardware-target-v1` JSON contains `top_module`, integer `parameters`, `ports`
(`name`, `direction`, `width`) and `clock`. These are declared integration inputs;
the agent cannot alter them. Select models/providers as described below. This
command incurs model charges shared across every planning and testbench call.
Optional `--knowledge-catalog` and `--allow-proposed-knowledge` work as in `plan`.
Allow at least six agent turns with KB, or four without. Testbench completion
requires specification search/read and RTL reading; cited blocks must have been read.

Every specialist receives the executor's sampling convention and observation limits:
one 10 ns clock, checks 1 ns before or after the final rising edge of each step,
declared output ports and optional read-only internal probes. A probe requires an
explicit `hardware-target-v2` entry such as
`{"name":"write_pointer","path":"wr_addr","width":3}` in `probes`. Paths are
relative to the DUT; the agent selects declared names and cannot invent paths or
drive probes. Missing paths and actual-width mismatches cannot pass simulation.
These are functional simulation conventions, not physical timing guarantees.

By default, execution readiness is decided per scenario. Plan questions and findings
block affected items; requirement questions and specification/analysis findings also block
other items using the affected requirements. New review findings explicitly identify
item, requirement, source, global or unknown scope. Local scope needs exact source
evidence and a rationale; unknown scope still blocks execution without claiming that
the problem is global. Historical unscoped findings and extraction warnings continue
to block all items. For free-text analysis gaps, the existing reviewer may perform
one additional assessment task using the same budget and source/KB tools. Every gap
must retain a disposition; narrowing it requires source quotations actually read.
The assessment cannot clear explicit questions or findings. Original evidence remains
unchanged, and proposed gap classifications still need quality evaluation.

An explicit `--experimental` run lets the testbench agent investigate cases blocked
only by unknown-scope review findings or analysis gaps. It must account for every
such issue and quote source text actually read to justify the independence of the
whole case, including setup transactions. An unresolved dependency returns
`needs_input`. Explicit scoped/global findings, design questions and extraction
warnings retain their execution gates. The original review/readiness remain
unchanged; a passing experiment does not clear blockers or grant engineering
acceptance. This mode uses the existing testbench task instead of the separate gap
classification task, retains the shared budget, and cannot be changed on resume.

Eligible scenarios proceed independently. A testbench proposal can report `needs_input`
without stopping other eligible items. Non-simulation methods remain unexecuted. A
mixture of passing and blocked/unsupported items reports `partial`; execution failures
report `failed` even alongside blocked items. Partial runs exit nonzero. Valid bindings
map every expected-result index, which checks mapping completeness, not check semantics.

The command prints a run ID. Repeat it with the original inputs/options and
`--run-id <id>` to resume. Completed agent tasks and simulation receipts are
validated and reused; changes to bound inputs, configuration or evidence fail.
`spend <id>` and `tasks <id>` cover the whole connected run. `result.json` retains
the existing planning result; `pipeline-result.json` links proposals, bindings and
simulation evidence. `readiness.json` lists item decisions and blocking reasons;
`readiness-inputs.json` binds those decisions to the original evidence and any
`execution-gaps.json` assessment. Default pipeline results use version 2;
experimental results use version 3 and retain pending engineering acceptance.
Historical planning exports and spending remain readable. Reports distinguish unexecuted items and never claim human
approval or measured functional coverage. Icarus must be installed before model
execution begins. Normal tests use mocked model replies and a real local simulator;
they do not establish live model quality.

## Directed testbench and simulation

The local `testbench` command consumes the existing specification, analysis and
plan JSON formats plus a `directed-testbench-v1` binding. The binding supplies the
RTL module, integer parameters, ports, initial inputs and clocked steps with
expected output values linked to the plan's expected results. These are authored
inputs; the command does not ask a model to infer hardware behavior or interfaces.
See the contract in `src/soc_verifier/domain/testbench.py`.

```bash
uv run soc-verifier testbench artifacts/plan.json \
  --source artifacts/specification.json --analysis artifacts/analysis.json \
  --binding artifacts/binding.json --rtl path/to/design.sv \
  --output artifacts/testbench-bundle
uv run soc-verifier simulate artifacts/testbench-bundle \
  --output artifacts/simulation-run --timeout 10
```

Use new output directories for every build/run. Install
[Icarus Verilog](https://steveicarus.github.io/iverilog/usage/installation.html)
(`iverilog` and `vvp`) for simulation. Both commands are local and make no model
calls. The runner executes explicitly supplied trusted RTL; it is not a security
sandbox or a general-purpose agent execution tool.

This slice supports standalone Verilog/SystemVerilog files, one clock with a
10 ns period, unsigned ports/probes up to 64 bits and literal expected values. Inputs
are driven while the clock is low. New `directed-testbench-v3` bindings let each
check select `phase: pre_edge` or `post_edge`, sampling 1 ns before or after the
last rising edge of its step. Earlier cycles in a multi-cycle step have no checks;
use one-cycle steps when each edge needs observation. Old V1/V2 bindings keep their
original output-only post-edge renderer. V3 supports declared internal probes with
plain hierarchical paths; memory indexing and expressions are unsupported.
It does not implement bus agents, UVM, multiple clocks, arbitrary assertions,
include/library configuration or functional coverage. Selected plan questions
need explicit resolutions before building; these do not confer engineer approval.

Bundles freeze the source/requirements/plan, binding, RTL and generated testbench
with hashes. Simulation copies those verified bytes, compiles and runs with process
timeouts, and saves tool versions, logs, a VCD waveform, `result.json` and
`summary.txt`. Compilation errors, failed checks, incomplete runs and timeouts
cannot pass. Unexecuted checks and unbound expected results remain visible. A
passing directed scenario is not full requirement or design coverage. External
simulator tests skip explicitly when Icarus is absent; other tests remain offline.

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

`SOC_VERIFIER_MODEL_API` selects `chat_completions` (the default) or `responses`.
The Responses route uses the native Agents SDK adapter with local conversation
history, function tools and structured output. It does not store a server-side
conversation or enable hosted tools. The exact `openai/gpt-6.1-terra` model requires
`responses` for this agent runtime; the application rejects its Chat Completions
configuration before inference. Model and provider selection stay explicit.
`SOC_VERIFIER_REASONING_EFFORT` is optional; leave it unset unless supported by
the selected model/provider. Terra defaults to medium effort on Responses.

To require source investigation before a planner finishes, set
`SOC_VERIFIER_PLANNER_SOURCE_LOOKUP=true`. The planner must search the full bound
source and read a matching block when results exist. This follows the KB search/read
when a catalog is enabled. Set `SOC_VERIFIER_AGENT_MAX_TURNS` to at least five with
KB, or three without; eight allows additional investigation. Invalid turn capacity
is rejected before the workflow starts model calls. These are minimum consultation
steps, not a guarantee that the relevant evidence was found or correctly applied.
The total call and cost limits still apply to every follow-up.

```bash
uv run soc-verifier plan artifacts/specification.json
uv run soc-verifier resume <run-id>
uv run soc-verifier resume <run-id> --workers 1  # Resume sequentially
uv run soc-verifier tasks <run-id> --json
uv run soc-verifier export <run-id> --output artifacts/verification_plan.xlsx
```

To run an explicit trial with the proposed public knowledge collection:

```bash
uv run soc-verifier plan artifacts/specification.json \
  --knowledge-catalog docs/knowledge/catalog.json --allow-proposed-knowledge
uv run soc-verifier knowledge <run-id>
```

The KB is Markdown plus a JSON catalog of entry IDs, content hashes and review
status. Without the provisional flag, only approved entries with a recorded
reviewer are eligible; the current catalog has none. Each run freezes its selected
entries in `knowledge.json`. All three specialists can search that snapshot by
keywords and read selected entries through bounded tools. There is no vector
database, automatic web browsing or reference-answer retrieval. Knowledge supplies
verification methods; the current specification supplies design facts.

Each KB-enabled invocation must search and, when matches exist, read guidance
before its output is accepted. API tool choice enforces those initial steps; the
model chooses the search query and which entries to read. The local `knowledge` command and the Excel
**Knowledge retrieval** sheet show actual accesses by role/task. These records
show retrieval, not proof that guidance was correctly applied to each plan row.
Changing the saved snapshot prevents resume; changing authoring files leaves
existing snapshots intact. Tool follow-ups consume the same run budget.

Source search returns excerpts around matching text and a `next_offset` for more
results. Full-block reads use character offsets. Local `source-access.*.json`
receipts bind task/invocation, source snapshot, returned IDs, offsets and excerpt
hashes. Table-header and neighboring-block context remain incomplete; source access
does not establish complete document coverage.

For the experimental SV-05 source-accounting workflow, add `--source-accounting`
to `plan` (and to `resume` for that run), or set `SOC_VERIFIER_SOURCE_ACCOUNTING=true`.
It defaults off and currently accepts only one bounded source chunk; larger
inputs fail before inference. The analyst records conditions, constraints and
exceptions and selects from precomputed source-passage IDs. Python copies exact
source quotations and locations from those IDs, preserves those fields in the
planner's requirements and exposes unaccounted text as unresolved. Dispositions
use the same passage IDs. Invalid overlapping or duplicate dispositions receive
one correction opportunity; every obligation and gap must stay unchanged.
Both attempts and validation feedback are saved, so resume does not renew this
allowance. All model requests use the existing run budget.

The existing reviewer first records an independent inventory of every source
passage, with no access to candidate requirements or dispositions. A second
invocation compares that inventory, the original source and the extraction, citing source
passages for omissions, lost qualifiers, unsupported claims and contradictions.
Findings remain advisory and visible in planning/export. The auditor can record
why a KB entry applies only if it actually read that entry during its task.
These judgments require review; an empty audit does not establish correctness.

```bash
uv run soc-verifier plan artifacts/packet.json --source-accounting \
  --knowledge-catalog docs/knowledge/catalog.json --allow-proposed-knowledge \
  --analysis-only
uv run soc-verifier accounting <run-id> --revision 0
uv run soc-verifier audit <run-id> --revision 0
uv run soc-verifier resume <run-id> --source-accounting
```

`--analysis-only` requires source accounting and stops after extraction/audit,
before paying for planning. It reports `analysis_ready` and creates no plan or
`result.json`. Resume without that flag to continue under the same configuration
and remaining budget. Omit the flag initially to run the complete workflow.
An extraction revision has three specialist invocations before planning (analyst,
independent inventory, comparison), plus at most one disposition correction.
Each invocation can make multiple model/tool calls, all under the existing budget.
The inventory and comparison are saved with their own input bindings and reused on
resume. The inventory accounts for passages; its facts still need semantic review.

The local `accounting` and `audit` commands inspect completed artifacts without
inference. Plan exports add **Source accounting**, **Source audit** and
**Knowledge application** sheets. Unknown IDs and stale bindings fail validation.
Passage boundaries are mechanical sentence/line splits; table rows stay whole.
Quotations prove location, not correct interpretation or complete extraction;
non-normative dispositions and audit findings require review. Historical V1/V2
accounting remains readable; runs without these artifacts report them unavailable.
The [auditor evaluation protocol](evals/source-audit-protocol.md) separates these
software checks from the outstanding quality measurements.

Monitor a run from another terminal with `uv run soc-verifier spend <run-id> --watch`.
It refreshes every five seconds and stops when the run completes; Ctrl-C stops
only the monitor. Omit `--watch` for a single snapshot. This command is local and
does not require an API key or make paid requests. It separates provider-reported
charges from outstanding reservations for in-flight or unknown charges, and shows
the remaining run budget and attempted-call count. Available budget must cover the
next full reservation before another request can start. An interrupted or
analysis-only run's monitor keeps watching until stopped. Older runs without a
ledger require their `events.log` instead. Account-wide spending and per-key filters are available in
[OpenRouter Activity](https://openrouter.ai/activity); an API key's spending cap is
separate from the account's credit balance and this application's per-run cap.

`uv run soc-verifier tasks <run-id>` reports each task's role/stage, calls,
failed invocations, billed charges and unsettled reservations. Add `--json` for
machine-readable output. Both reporting commands are read-only and need no API key.
Legacy ledgers retain their totals with task attribution explicitly unavailable.

Every run gets its own directory under `artifacts/runs/`. JSON artifacts are
immutable and authoritative; Excel is a review view. Exports refuse existing
targets. A clean automated review produces `draft_ready`, never human approval
or a claim that hardware has been verified. Findings, source gaps, extraction
warnings or open questions produce `needs_review`.

Review schema 2.0 records defect kind, scope, evidence and a recommended action;
historical schema 1.0 remains readable and exportable without guessing missing scope.
These are proposed judgments, not engineering approval or demonstrated accuracy.
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
worker count, agent turn limit (default 4 per invocation), total attempted model calls
and dollar budget (default $2/run). SDK retries are disabled; failed calls consume
the same attempt budget. Tiered endpoint pricing currently fails preflight rather
than using an incomplete cost estimate.
One batch is executed at a time by default; increase `BATCH_WORKERS` explicitly
for bounded concurrency. `resume --workers 1` overrides scheduling for that
execution without changing the saved manifest, prompts, or budget.
Changing output-token limits requires a new run: even a lower ceiling can change
splitting, calls and results. The retained `--max-output-tokens` option accepts only
the original value. Resume rejects changes to source bytes, task assignments,
prompts, schemas, tools, installed runtime code/dependencies and behavior settings.
Worker scheduling remains adjustable. HTTP failures
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
    runtime.py             # SDK Runner, bounded turns, explicit evidence snapshots
    tasks.py               # Versioned task inputs and content-bound checkpoints
    attempts.py            # Invocation-local call attribution and reasoning replay
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
stage decisions, validates exact input fingerprints and executes only unfinished tasks.
Each completion receipt atomically binds the result to its inputs; missing canonical
JSON projections can be recovered from the receipt without another model call.
Split markers bind the exact assigned IDs and content, including child partitions.
An interrupted agent task restarts its tool conversation; earlier remote calls may
already have been charged and remain in the ledger. There is no exactly-once billing
guarantee. The application is a single process; multiple processes must not execute
the same run concurrently. SQLite/PostgreSQL graph checkpoint support and the
`postgres` extra have been removed.

## Reviewing the Agents SDK migration

The `migration/openai-agents-sdk` branch has been merged into `main`.
Commit `10f5bad` preserves the tested prototype; inspect the migration with
`git diff 10f5bad..5d15c10`. The merge includes the preserved prototype changes.

Prompt version 5 and engine `openai-agents-v2` identify task-aware runs. Earlier runs
remain exportable and readable by `spend`, but cannot resume under this runtime.
Use the baseline checkout and its locked environment for an unfinished legacy run.
Run manifests/results are version 2.0; application source/analysis/plan/review
schemas remain 1.0. Legacy exports mark new task metadata unavailable.
The four available tools are `search_spec`, `get_source_blocks`,
`get_requirements` and `get_plan_items`. They read only the task's explicitly bound evidence revisions.
The analyst has source tools; the planner additionally retrieves requirements;
the reviewer additionally retrieves full plan scenarios. `events.log` records
agent starts, tool names, model-call usage (including reported cache/reasoning
tokens) and completion. It does not log tool arguments or evidence text.

OpenRouter reasoning blocks are preserved unchanged across tool follow-ups within
an invocation, including ordered encrypted/signed metadata. Histories that cannot
be matched safely are rejected before another paid request. This adapter behavior
is a separately versioned comparison condition; it is not proof of compatibility
with every live model/provider. Model routing and caching optimization remain deferred.

The transport passes already-decoded response bytes to the SDK with rebuilt
encoding/length headers. Compressed provider replies are decoded once; their
usage is accounted before local validation, including failed generations.

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
