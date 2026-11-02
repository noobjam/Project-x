# Architecture

## Runtime and boundaries

SoC Verifier uses the OpenAI Agents SDK for agent execution and the OpenAI Python
client through OpenRouter for inference. LangGraph/LangChain and their database
checkpointers are removed. Domain contracts remain independent of either SDK.

```text
CLI -> PlanningWorkflow -> AgentRuntime -> OpenAI Agents SDK Runner
                            -> analyst / planner / reviewer
                            -> read-only evidence tools
                            -> OpenAI client -> budgeted OpenRouter transport
    -> domain validation -> immutable artifacts
    -> export -> canonical JSON -> Excel
```

`agents/analyst.py`, `planner.py` and `reviewer.py` construct actual SDK `Agent`
objects with instructions, tools and typed outputs. `agents/runtime.py` executes
`Runner.run`; the model chooses whether to call tools, consumes their results and
continues until a final artifact or the turn limit. Python selects the specialist
and task, validates source/requirement references, controls revision routing and
publishes artifacts. There are no model-directed handoffs or manager agent.

`providers/` owns OpenRouter routing, credentials, diagnostics and spending.
The gateway uses a budgeted async transport backed by the shared HTTP client.
Every SDK request, including each tool follow-up, reserves cost before inference
and settles from reported usage before output validation. SDK retries and OpenAI
trace export are disabled. The gateway pins the configured model/endpoint,
disables fallback and retains the current deny-data-collection/ZDR policy.
The client SDK does not imply OpenAI-hosted inference or an OpenAI API key.
Automatic model selection and per-role model settings are not implemented.

`model_api` selects the native SDK Chat Completions or Responses adapter. Responses
is opt-in and supports stateless, non-streaming text with local function tools;
remote conversation state, hosted tools and multimodal input are rejected. Full
tool history and opaque encrypted reasoning are replayed by the SDK. The transport
enforces `store=false`, disabled truncation and the configured output limit, then
records usage before rejecting partial/refused output. API mode and reasoning
settings are bound into task configuration; changing them requires a new run.

## Agents and tools

An optional knowledge catalog enables `search_knowledge` and
`get_knowledge_entries` for all three specialists. The run stores an immutable
`knowledge-snapshot-v1` JSON artifact, inherited by every task and child batch.
The catalog hashes Markdown entries and records proposed/approved status;
approved entries require a reviewer, and proposed entries require explicit trial
opt-in. Search returns at most five matches per page; reads return at most four
entries and 4,000 characters per entry, within the shared tool response bound.
The runtime requires search, then a read when there are matches, through API tool
choice; after consultation the model can choose further tools or finish. A final
guard rejects providers that ignore required consultation. The runtime records
`knowledge-access-v1` events by task/invocation, entry hash and character offset.
These are access records, not per-item application claims. Guidance is untrusted
methodology, never specification evidence or permission to execute tools.
When `planner_source_lookup` is enabled, planners must also search the full bound
source and read a matching block when results exist. No-hit searches can proceed.
A read must include an ID actually returned by a search. The workflow rejects
insufficient turn capacity before extraction starts: at least five turns with KB,
or three without, including final output. The model still chooses queries and
reads; enforced consultation alone cannot establish relevance or correctness.
Forced function turns use the function's argument schema without a simultaneous
final-output response schema; automatic/final turns retain the artifact schema.
Integer bounds outside JSON's interoperable exact-integer range are represented
as exact textual constraints in the provider schema. Local domain validation keeps
the original numeric limits; ordinary schema constraints remain intact. Provider
error codes and the known oversized-schema-number error are recorded without raw
upstream payloads that could contain private inputs.

| Agent | Responsibility | Tools |
| --- | --- | --- |
| Requirements analyst | Extract grounded requirements and investigate system interactions | `search_spec`, `get_source_blocks` |
| Verification planner | Develop scenarios for assigned requirements | Source tools, `get_requirements` |
| Verification reviewer | Investigate omissions, unsupported details and weak scenarios | Source/requirement tools, `get_plan_items` |
| Testbench agent | Propose directed input sequences and expected-value checks for one generated plan item | Source/requirement/plan tools, `read_rtl` |

Tools read the current run's specification and validated artifacts. Context is
injected locally by the SDK and is not automatically serialized into prompts.
Search is deterministic word matching, not semantic retrieval. Search results
contain match-centered excerpts with exact character offsets and stable pagination
through `next_offset`; source reads support character pagination with explicit
continuation offsets. `source-access-v1` receipts bind the task/invocation and
source snapshot to returned IDs, offsets and excerpt hashes without copying text
into the receipt. Supported table-header and neighboring-block access remain
unfinished. Retrieval rejects unknown IDs, has an ID-count limit and
bounds output size. Tools cannot read arbitrary paths, run shell commands, call
external services or grant approval. Source and tool text remain untrusted evidence.

The model can request tools autonomously within its assigned task. It cannot choose
the next workflow stage, raise its budgets or turn a draft into engineering signoff.
A tool loop may increase cost; bounded input and measured usage matter more than
calling something an agent. `AGENT_MAX_TURNS` defaults to four per invocation, including
the final-output turn. Total attempted model calls and dollar limits are shared
across all workers, tasks and corrections.

## Workflow and durability

```text
Source chunks -> analyst tasks -> exact merge -> system analyst
             -> planner tasks -> local reviewers -> system reviewer
             -> targeted revision or final draft
```

Every source block belongs to a primary extraction/review chunk; relevant table
headers are included. Exact deduplication preserves distinct and conflicting
requirements and derives stable IDs from statement, feature and basis. Global
analysis adds requirements and cannot delete local ones. Planning batches must
cover every assigned requirement; item IDs are namespaced before review.

Local planning/review receives local evidence plus a small requirement directory.
Global passes receive section outlines, requirement indexes and (for review) a
compact plan index. Agents retrieve original evidence/full scenarios when needed.
The complete source is no longer repeated in both global prompts. This changes
engineering behavior and requires fresh quality evaluation; retrieval is not a
proof of completeness or semantic correctness.

Review findings target `analysis`, `plan` or `specification`. Repairable errors
route to analysis/planning with a shared revision maximum. Source ambiguities stay
visible for an engineer rather than triggering repeated attempts to invent answers.
Warnings, gaps, extraction warnings and open questions yield `needs_review`.
A clean automated result is `draft_ready`; `human_approved` remains false.

New planning reviews use schema 2.0 with defect kind, recommended action and explicit
item/requirement/source/global/unknown scope. Local scopes require exact quotations
from the bound specification and a rationale. Python validates references and quoted
text; neither establishes semantic correctness. Missing obligations can cite sources
without inventing requirements or scenarios. Local review summaries feed integration
review, with at most 64 entries and explicit omission counts; all original findings
remain in the combined review. Historical schema 1.0 readers and exports are retained.

Immutable JSON artifacts are the recovery checkpoints. On restart, Python replays
the deterministic stage/revision decisions and validates/reuses completed outputs.
Batches publish independently, so completed batches survive interrupted stages.
Each role, batch, split child and system pass has an opaque task ID. Its fingerprint
binds ordered assignments, exact artifact names/byte hashes, input content, schema,
prompt/tool/source-processing versions, installed source/dependency versions and
behavior settings. Tools receive explicit source/analysis/plan references rather
than searching for the latest revision. Completion receipts bind and publish the
result atomically; canonical output files can be restored without inference.
Split markers bind the parent fingerprint and exact inputs, not merely item counts.
An unfinished agent task restarts its conversation; completed tool/model turns
inside it are diagnostics, not resumable SDK sessions. Their charges remain in the
ledger. Multiple processes must not execute one run concurrently; no distributed
lock or exactly-once inference/billing guarantee is provided.

Output-truncated local tasks are bisected; persistent split markers prevent
repeating a known oversized parent. Unknown chunk citations, planner coverage
errors and invalid review item references receive at most one explicit correction
per execution. Schema, transport, refusal, single-item overflow and exhausted
agent-turn limits stop without accepting partial output. Canonical artifacts are
published only after domain validation. Rejected responses remain diagnostic files.

For C source chunks and B planning batches, a large run starts `2*C + B + 2` agent
tasks before corrections/revisions. Each task may make several model requests.
Small inputs start three tasks. All follow-up requests use the same cost/call ledger.

### Bounded source-accounting experiment

SV-05 is opt-in through `source_accounting`. It currently rejects multi-chunk
source packets before inference; planner and reviewer batching still work.
The analyst returns `source-accounting-draft-v3`: obligations with conditions,
constraints, exceptions and selected passage IDs, plus grouped proposed
non-normative/unresolved passage dispositions. Python precomputes exact sentence/line
passages (whole table rows) and constrains evidence choices to those IDs in the
output schema. These mechanical boundaries do not classify normative behavior.
Python copies the corresponding quotations and Unicode code-point spans with
complete block-text hashes and computes unaccounted passages. Evidence and
dispositions use the same scope, including when a paragraph mixes requirements
and informative references. Nonexistent evidence fails; duplicate dispositions
or classifying an evidence passage as non-normative produces structured feedback.
It does not infer whether the quoted text semantically supports the requirement.

`obligations.rNNN.attempt0.json` checkpoints a returned draft before domain
acceptance. A repairable disposition error writes versioned feedback and permits
one `attempt1`, bound to the rejected draft and feedback. Every obligation, its
ID/facts/evidence, and every gap must remain unchanged. Both attempts persist and
are replayed on resume; exhausted correction cannot renew itself. A task interrupted
before returning still follows the existing unfinished-task restart rules and budget.
Only domain-valid output reaches the canonical `obligations.rNNN.json` completion.
Python projects all structured facts into V1 requirement statements without a
second model pass. `source-accounting.rNNN.json` binds the exact specification,
raw extraction and projected analysis bytes using `source-accounting-v3`. Its
status remains unreviewed. Earlier V1 quote-based and V2 block-disposition reports
remain readable without mutation.
Unaccounted/unresolved source adds visible analysis gaps; the opt-in batched
planner/reviewer also receives those gaps. Downstream tasks bind the accounting
snapshot, and interrupted projections are recreated from validated completions
without recharging extraction. The local CLI and Excel export verify the same
bindings. Existing source, analysis, plan and review schemas remain unchanged.

The reviewer role performs two separate invocations after each extraction revision
and before planning. First, `source-inventory-v1` records explicit facts or a
context/unresolved classification for every supplied passage. This task receives
only source and optional KB references; requirement/plan tools have no candidate
to return. It does not inherit the analyst's dispositions or any reference answers.
The host rejects missing, duplicate or invented passage IDs. Complete passage
accounting does not prove complete or correct understanding.

The comparison invocation receives the exact inventory, source, analysis and
accounting. Its output is projected into the existing `source-audit-v1` artifact.
Inventory and comparison receipts are persisted independently; interrupted
execution reuses completed stages. Reads validate the source-only inventory
binding, comparison parent/input references, identical projected output and actual
comparison-task KB reads. Earlier audits without this mode remain readable.
Its findings identify source passages and affected
requirements; an omission can lack a requirement ID. A conflict requires two
distinct cited passages, subject, conditions and an incompatibility explanation.
Known IDs prove location only. Python cannot establish whether the statements
actually conflict or an omitted obligation is real.

KB application records identify requirements/passages, applicability and rationale.
Their entry IDs must exist in the frozen snapshot and in that audit task's actual
read records. This validates access, not the correctness of the claimed application.
All findings and application judgments remain `agent_proposed`. Invalid references
halt before planning; semantic findings are initially advisory. They enter planner
context, filtered by assigned requirement IDs for batches, with global omissions
retained. Planner guidance requires source checks and visible uncertainty. Any
finding or uncertain application keeps the final result at `needs_review`, even
if the later plan review is clean. The audit does not repair extracted facts.

`--analysis-only` stops after extraction/audit with `analysis_ready` and no plan
or `result.json`. It is a stopping point, not a changed task input: a later resume
can continue planning with the same artifacts and budget. This opt-in path starts
three specialist invocations in analysis-only mode or at least five for a complete
small run, plus one possible disposition correction. Each invocation may require
several tool turns; the existing aggregate call/cost caps are unchanged.
The CLI `audit` command and Excel sheets expose the findings without inference.
See the [calibration protocol](../evals/source-audit-protocol.md) before interpreting
these artifacts as evidence of quality.

## Spending and migration compatibility

Chat Completions reservations use advertised endpoint context capacity and output
ceiling at pinned token prices; tiered prices remain unsupported on that route.
Responses uses a conservative request estimate covering serialized instructions,
schemas, tools and complete history: twice the UTF-8 byte count plus a framing
allowance. It selects the highest advertised input/cache and output rates across
recognized tiers, rejects unknown fee structures, and pins pricing across resumes.
This is an estimate, not an exact provider token count or provider-enforced dollar
cap. Large tool histories can exhaust admission headroom even when reported charges
are small. Each call settles against its own persisted reservation.

Unknown charges remain reserved across restarts. Only a confirmed OpenRouter
in-flight admission rejection settles at zero. Pricing changes or reported billing
above the reservation stop the run. These controls do not replace an account-level
credit/key cap.

Runs pin engine, prompt version, model, provider and generation limits. Only worker
scheduling can change on resume; changed output ceilings require a new run. Prompt
version 7 added enforced knowledge consultation; version 11 introduced passage
dispositions, mechanical feedback and the advisory source audit to the opt-in
path. Those audit revisions left normal specialist instructions unchanged. Opt-in planning appends
explicit guidance for handling provisional audit findings.
Version 12 adds source-specific audit ID enums and confines extraction defects
to differences supported by the actual source. Missing optional checklist detail
does not by itself establish an extraction defect. The audit remains fallible
and advisory; calibration results are separate from these software constraints.
Prompt 15 requires concrete stimulus, observation and discriminating expected
results, and source investigation of missing design details before planning is
finalized. Tool version 5 records the changed retrieval behavior and source access.
Engine `openai-agents-v2` identifies
task-aware runs. Version 2.0 run
manifests/results coexist with unchanged 1.0 domain schemas. Legacy completed plans
remain exportable with new metadata marked unavailable; `spend` and `tasks` read
old ledgers without rewriting or inferring missing attribution. Unknown task,
completion, execution and result versions fail explicitly. SQLite and PostgreSQL
checkpoint files remain intact but are not read by this runtime.

Every SDK invocation has an ID under its task. Every model request, including tool
follow-ups, has a call ID; reservations carry both identities and the effective
request hash. Failures retain safe error types, and interrupted invocations remain
visible. Thread-local asynchronous context propagation keeps concurrent attribution
separate. `soc-verifier tasks RUN_ID [--json]` reconciles task charges and unsettled
reservations separately against the existing ledger.

For Chat Completions, the OpenRouter transport restores `reasoning_details` and plaintext reasoning onto
the corresponding assistant tool-call messages before follow-up requests. It retains
opaque values and block order, isolates histories per invocation, and rejects
ambiguous histories before inference. Plain calls without reasoning metadata keep
their existing request behavior. Reasoning replay is recorded as `openrouter-v1`
and must be declared separately in model comparisons. Responses uses native SDK
encrypted-reasoning replay instead of this Chat-specific reconstruction. Offline SDK tests validate
serialization; live endpoint feasibility remains an SV-10A gate before model selection.

Operational logs contain agent/tool names and numeric usage, including cache and
reasoning token counts when reported. They exclude document/tool text. Local model-output
artifacts contain sensitive source-derived content and are never treated as valid
plans. Credentials/specifications/generated outputs remain ignored by Git.

## Validation and next capabilities

Offline tests exercise the real OpenAI SDK and Agents SDK tool loop against a
simulated OpenRouter API, plus domain contracts, source retrieval, revisions,
restart behavior, usage accounting, failed responses and budget/turn limits.
They establish software behavior, not model quality, live provider compatibility
or savings. Normal CI remains offline; engineering validation is tracked separately.

Before selecting models, compare source accuracy, missed requirements, unsupported
claims, interaction scenarios, reviewer effort and cost on engineer-labelled cases.
The human reference VPlan is evaluation material and is not supplied to agents.
`workflows/verification.py` connects the existing planning workflow to the
testbench specialist and `workflows/plan_to_simulation`. `verify` takes source,
declared hardware and RTL, without an authored plan or binding. One runtime and
budget ledger span all model calls. A bound hardware snapshot makes the declared
interface/configuration visible to planning and provides read-only RTL to the
testbench agent. The agent must read source/RTL before returning literal checks;
the host validates references, directions, widths, questions and expected-result
mappings before rendering and simulation. The model has no execution tools.
All specialists also receive `directed-execution-v2`: the renderer's shared timing
constants, declared output ports and optional read-only internal probes. Sampling
delays are explicitly testbench conventions, not new DUT requirements. The planning
gate still preserves unresolved questions and checks outside these capabilities.

Testbench tasks use `agent-task-v2`; existing specialist tasks remain V1. New
`testbench-proposal-v2` outputs become `directed-testbench-v3` bindings with task
and proposal hashes. Every check selects `pre_edge` or `post_edge`, 1 ns before or
after the final rising edge of a step. Input driving occurs at the beginning of
the low phase and inputs hold between these samples. Earlier cycles in a step are
not sampled. Source validity conditions still apply, including unspecified outputs.
`hardware-target-v2` may declare up to 64 read-only probes (name, relative path,
unsigned width 1–64); the agent can select aliases but cannot add or drive probes.
Only plain hierarchical identifiers are accepted. The V2 renderer checks actual
probe widths with `$bits`; missing paths, X/Z values and failed comparisons cannot
pass. Simulation result V2 includes check phase; declared bindings retain paths.
This does not implement arbitrary timing, memory indexing or multiple clocks.
V1 proposals, V1/V2 bindings and their byte-identical V1 renderer remain readable.
Bundles pin the generator and reject a mismatch. `pipeline-result.json` is separate from the original planning
result and links each item to its proposal, binding and hashed simulation evidence.
`execution-readiness-v2` computes per-item eligibility from explicit issue references
and distinguishes mapped, global and unknown review impact. Version 1 remains readable.
Plan-local findings stay local; requirement questions and specification/analysis
findings propagate to every consumer of the affected requirements. Source-only
findings conservatively map all consumers of those blocks; an unrepresented source
remains unresolved. In default execution, global and unknown findings both block
all items, with distinct recorded reasons; legacy empty item lists retain unknown
scope and continue blocking.
Extraction warnings and unclassified analysis gaps still block all items. Source-audit
findings and uncertain knowledge applications retain their requirement scope.

When free-text gaps are the remaining obstacle for a simulation item, the existing
reviewer performs one `execution-gap-assessment-v1` task, with required source and
enabled KB consultation under the same budget. It must account for every gap once.
Narrowed scopes/notes require exact quotations within source spans actually read;
unknown scope stays global. This proposed judgment cannot clear other explicit
blockers or establish engineering approval. No new agent role is added.

An opt-in experimental path leaves these readiness decisions intact and permits
the existing testbench agent to investigate a case whose only blockers are
unknown-scope review findings or unclassified analysis gaps. The task receives all
applicable issues and full original review findings. `testbench-proposal-v3` adds
case-level assessments with exact issue accounting, source quotations actually
read, and reasoning about setup as well as expected values. An unresolved issue
requires `needs_input` without executable steps. Explicit mapped/global findings,
questions, extraction warnings and source-audit issues cannot use this path.
The host checks quotation/reference validity, not semantic independence; these
remain proposed judgments. Original evidence and blockers are never rewritten.

Experimental execution/results use V3, with case receipts V2 and engineering
acceptance explicitly pending. The generated binding/rendering contracts remain
V3/V2. Tests may pass while readiness stays blocked, so overall completion remains
partial whenever those issues persist. Experimental tasks replace the standalone
gap classifier; no extra role or review loop is added. The execution mode is pinned
before planning and included in testbench task evidence, preventing mode changes on
resume. Default execution/result contracts and historical proposal readers remain.

Default pipeline execution/results use version 2 and bind readiness inputs, decisions and
agent tasks. Unaffected items can proceed while blocked items and unsupported methods
remain unexecuted. A testbench `needs_input` does not stop subsequent eligible items.
Mixed passing/pending results are partial, while execution failure takes precedence.
Completed stages are reused only after validating their evidence. Historical planning
contracts and spending readers remain supported.
Broader testbench environments, JEV and coverage closure remain future work.

## Upstream references

- [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents-sdk)
- [OpenRouter with the OpenAI SDK](https://openrouter.ai/docs/quickstart#using-the-openai-sdk)
- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)

- [OpenRouter reasoning preservation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
