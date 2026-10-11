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

The graph is `analyze -> plan -> review -> finish`, with a bounded `review -> plan`
edge for error findings. Completed node outputs are saved before checkpointing.
Replayed nodes reuse validated saved artifacts. Each run pins its model, endpoint,
prompt version and generation limits; changing them requires a new run.

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
