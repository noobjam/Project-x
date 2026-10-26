# Architecture

## Scope

One installable Python package, one process, one implemented workflow. The domain
is system-level verification; the first capability is specification-to-plan.
Workflow stages currently make bounded structured LLM calls. Dynamic tool search,
autonomous EDA operation and test generation are not implemented.

## Dependency direction

The `domain` package depends on Pydantic, not LangGraph or provider SDKs. Ingestion
and export consume domain contracts. Workflow nodes consume `StructuredLLM` and
the artifact store. `cli.py` supplies the concrete OpenRouter transport and
checkpoint backend. Credentials and provider request fields stay outside prompts
and graph state. Ordinary node functions make this boundary testable.

```text
CLI -> ingestion -> Specification
CLI -> workflow -> StructuredLLM <- OpenRouterLLM
              -> domain validation
              -> artifact store
              -> LangGraph checkpointer
CLI -> export -> JSON artifacts -> Excel
```

The application owns source IDs, reference validation, artifact revisions, run
configuration and stopping conditions. The model interprets engineering evidence
and proposes artifacts; it cannot assign human approval or verification signoff.

## State and durability

Each source block has a document hash and an XML locator. References are stable
within a document revision; alignment across edited document versions is not yet
implemented. Requirements and scenarios have string IDs; revisions live in
separate immutable JSON files. Source and requirement links are checked in Python.

The graph is `analyze -> plan -> review -> finish`. Review findings name the
affected artifact: `analysis` errors route back through the analyst and planner;
`plan` errors route to the planner. Missing specification information remains
visible for human resolution and does not cause futile retries. Both repair
paths share one revision budget. Large inputs execute bounded calls inside these
nodes, with each completed batch published as an immutable artifact before the
node completes. Batch worker threads share the same provider adapter and cost
ledger; they are instances of a role, not autonomous tool-using agents.

```text
Source blocks -> deterministic chunks
  -> analyst per chunk -> exact merge -> system interaction analysis (additions only)
  -> planner per requirement batch (global index + original supporting evidence)
  -> reviewer per source chunk -> global integration reviewer
  -> targeted revision or final draft artifacts
```

Every original source block belongs to one primary chunk; table headers are also
supplied as context. Empty/non-normative chunks are allowed. Merging combines only
identical normalized statements with the same feature and basis, unions their
evidence and questions, and retains distinct/conflicting requirements. Requirement
IDs are deterministic hashes of that identity. A global analyst adds grounded
cross-component requirements but cannot delete local requirements. Planning
batches must cover all their assigned requirements; their item IDs are namespaced
before review. Local review visits even chunks with no extracted requirements.
Global review checks integration using the original SPEC and compact indexes.
Output-truncated local analysis, planning and review tasks are recursively
bisected. Split markers and child artifacts survive restart; non-truncation
failures are not automatically retried. A single indivisible item or global-pass
overflow still fails explicitly. No partial JSON is accepted. Chunk analysis with
unknown source citations gets at most one corrective call per execution of that
chunk, using the original evidence and rejected candidate. A second invalid result
stops; no deterministic ID substitution is used. Schema, transport, and other
validation failures still stop without automatic retries.

For C source chunks and B planning batches, an initial large run makes
`2*C + B + 2` model calls before any adaptive splits or revisions. Small
specifications retain the three-call path.
Character limits, output limits, revision count, total request attempts and a
shared dollar budget bound the work. Before sending a request, the adapter reserves
the endpoint's advertised worst-case text-token cost; reported usage settles it.
Uncertain charges retain their reservation across restarts. Provider billing that
exceeds its advertised bound stops the run; this is not an account-level credit cap.
Global context is still bounded by the selected model's capacity. Hierarchical
global indexes for substantially larger systems are not implemented.

Analysis, plan and review revisions are immutable; `result.json` names the final
analysis revision, so exports never silently use superseded requirements.
Completed node outputs are saved before checkpointing.
Replayed nodes reuse validated saved artifacts. Each run pins its model, endpoint,
prompt version and generation limits; changing them normally requires a new run.
An explicit `resume --max-output-tokens` override may lower the original output
ceiling for unfinished work. It is logged, preserves all source evidence and
retains the original conservative cost reservation; it cannot increase the ceiling.
The `resume --workers` override changes scheduling only and is logged per execution;
it does not alter the original manifest or the shared cost ledger. HTTP failures
retain sanitized messages and allowlisted reason metadata for billing diagnostics.
Prompt version 3 added chunked role execution. Version 4 clarifies that review
item references are plan IDs for every finding target and allows one explicit
correction for invalid IDs in small, chunk and system reviews. The original
evidence and rejected review accompany validation feedback; a second invalid
response stops. Corrections use the same shared cost/call budgets. Older runs
remain exportable but must not be resumed under the new prompts.
Planning execution also provides one validation-feedback repair for missing or
unknown requirement references. It uses the same versioned planner instructions
and original assigned evidence, saves only a traceability-valid batch, and logs
the correction. Existing valid artifacts keep their meaning and are reused.

SQLite persists local checkpoints. PostgreSQL support is an optional extra and
requires an external database. Both contain specification content, so they require
the same access controls as the source files. LangGraph checkpoints are operational
state; domain JSON artifacts remain the source of truth. No distributed run lock
or exactly-once remote model billing guarantee is claimed.

## Adding subsequent capabilities

Test generation will consume accepted plan revisions, source-linked requirements
and an explicit RTL/testbench environment contract. Add a new workflow module and
typed artifacts for that capability. Simulation will use a separate tool adapter
and worker boundary so licenses, timeouts and process isolation are explicit.
Executions and coverage evidence will link back to scenario and requirement IDs.

Do not create empty future modules, a plugin registry or a second orchestration
framework in anticipation. Add a boundary when a real capability needs it. A CLI
or future API must use the same contracts and workflow functions.

## Evaluation

Software tests use synthetic source snippets and fake LLM outputs. They establish
contract enforcement, revision limits, persistence and routing, not ASIC planning
quality. Use the supplied human VPlan as a reviewed development reference, outside
the generation context. Independent held-out systems are needed before making
generalization claims. Track missed requirements, unsupported claims, source
accuracy, useful interaction scenarios, reviewer effort and cost.

## Upstream references

- [uv project structure and lockfile](https://docs.astral.sh/uv/concepts/projects/layout/)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [OpenRouter structured output](https://openrouter.ai/docs/guides/features/structured-outputs)
- [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)

Structured output behavior is endpoint-dependent; schema validation and engineering
validation remain application responsibilities. The current character limit is a
transport guard, not a model-specific token estimator.
