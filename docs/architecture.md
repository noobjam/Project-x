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
Forced function turns use the function's argument schema without a simultaneous
final-output response schema; automatic/final turns retain the artifact schema.

| Agent | Responsibility | Tools |
| --- | --- | --- |
| Requirements analyst | Extract grounded requirements and investigate system interactions | `search_spec`, `get_source_blocks` |
| Verification planner | Develop scenarios for assigned requirements | Source tools, `get_requirements` |
| Verification reviewer | Investigate omissions, unsupported details and weak scenarios | Source/requirement tools, `get_plan_items` |

Tools read the current run's specification and validated artifacts. Context is
injected locally by the SDK and is not automatically serialized into prompts.
Search is deterministic word matching, not semantic retrieval. Search results
contain bounded previews; source reads support character pagination with explicit
continuation offsets. Retrieval rejects unknown IDs, has an ID-count limit and
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
The analyst returns `source-accounting-draft-v2`: obligations with conditions,
constraints, exceptions and selected passage IDs, plus grouped proposed
non-normative/unresolved block dispositions. Python precomputes exact sentence/line
passages (whole table rows) and constrains evidence choices to those IDs in the
output schema. These mechanical boundaries do not classify normative behavior.
Python copies the corresponding quotations and Unicode code-point spans with
complete block-text hashes, rejects nonexistent evidence and contradictory
dispositions, and computes unaccounted text intervals.
It does not infer whether the quoted text semantically supports the requirement.

The immutable `obligations.rNNN.json` task completion is validated before planning.
Python projects all structured facts into V1 requirement statements without a
second model pass. `source-accounting.rNNN.json` binds the exact specification,
raw extraction and projected analysis bytes using `source-accounting-v2`. Its
status remains unreviewed. Earlier V1 quote-based accounting remains readable;
new calls select IDs because the initial live trial corrupted retyped quotations.
Unaccounted/unresolved source adds visible analysis gaps; the opt-in batched
planner/reviewer also receives those gaps. Downstream tasks bind the accounting
snapshot, and interrupted projections are recreated from validated completions
without recharging extraction. The local CLI and Excel export verify the same
bindings. Existing source, analysis, plan and review schemas remain unchanged.

## Spending and migration compatibility

Reservations use advertised endpoint context capacity and output ceiling at pinned
token prices. Unknown charges remain reserved across restarts. Only a confirmed
OpenRouter in-flight admission rejection settles at zero. Pricing changes or
provider billing above its advertised bound stop the run. Tiered endpoint prices
are currently rejected because the reservation calculation cannot bound them.
These controls do not replace an account-level credit/key cap.

Runs pin engine, prompt version, model, provider and generation limits. Only worker
scheduling can change on resume; changed output ceilings require a new run. Prompt
version 7 added enforced knowledge consultation; version 10 adds the opt-in
structured accounting analyst. Existing planner/reviewer instructions are unchanged.
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

The OpenRouter transport restores `reasoning_details` and plaintext reasoning onto
the corresponding assistant tool-call messages before follow-up requests. It retains
opaque values and block order, isolates histories per invocation, and rejects
ambiguous histories before inference. Plain calls without reasoning metadata keep
their existing request behavior. Reasoning replay is recorded as `openrouter-v1`
and must be declared separately in model comparisons. Offline SDK tests validate
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
or savings. No paid model run is part of this migration's validation.

Before selecting models, compare source accuracy, missed requirements, unsupported
claims, interaction scenarios, reviewer effort and cost on engineer-labelled cases.
The human reference VPlan is evaluation material and is not supplied to agents.
JEV, RTL/test generation, simulator tools and coverage closure remain future work.

## Upstream references

- [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents-sdk)
- [OpenRouter with the OpenAI SDK](https://openrouter.ai/docs/quickstart#using-the-openai-sdk)
- [OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)

- [OpenRouter reasoning preservation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens)
