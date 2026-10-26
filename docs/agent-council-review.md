# Agent roadmap council review

26 October 2026. Scope: revise the implementation plan before application changes.
The current proposal is [the agent roadmap](agent-roadmap.md).
This is the historical review record. Current ticket status, decisions and next
actions are maintained in [project progress](progress.md).

The council reviewed evaluation relevance, architectural feasibility and delivery
cost independently. Its recommendation is a smaller first release centered on
the Management CPU DOCX, with evidence and evaluation before speculative expansion.
Agreement among agents is design review, not engineering validation of generated
verification plans.

## Findings and resolutions

| Finding | Evidence or consequence | Resolution in the revised roadmap |
| --- | --- | --- |
| The primary workload was missing from the acceptance path. | The previous SV-01 started with several OpenTitan IPs and a new adapter. Public peripheral results cannot establish usefulness on the actual DOCX. | Management CPU is the acceptance anchor. One UART fixture and one focused integration packet support it. |
| Evaluation happened after almost all implementation. | SV-10 depended on review, repair and export completion. Multiple changes would be inseparable. | SV-10 now runs across delivery: baseline, comparisons after behavior changes, optional repair experiment and full-DOCX acceptance. |
| The first release was too broad. | Full source dispositions, atomic schemas, relationship modeling, patterns and repair all preceded acceptance. | First release is retrieval, structured findings, task/cost reporting and a review view. Later experiments require measured remaining failures. |
| Expert labels were assumed available. | No designated design/DV reviewer is committed. Agent suggestions and reference plans are not approved labels. | Explicit label provenance/status. Offline work may proceed; semantic acceptance remains pending when review is unavailable. |
| Reference exposure and exclusions could inflate results. | The private reference was previously inspected. Missing images/tables do not cease to be in scope. | Treat existing references as development/acceptance regressions. Show missing evidence, provisional labels, disputes and exclusions separately. |
| A mutation acceptance criterion was ambiguous. | Deleting behavior from the source may legitimately change the answer. | Remove obligations from agent output while source and reviewed inventory remain fixed. Source mutations get versioned expected labels. |
| SV-03 combined too many contract changes. | Source spans, task binding, obligation granularity, check identity, findings and migration formed one gate. | Freeze minimal conventions first. Keep current plan/requirement shapes; implement typed findings with SV-07 and defer semantic redesign. |
| Repair identity was unresolved. | Requirement IDs hash statement/feature/basis; plan IDs depend on batch position. Analysis edits can change IDs and unrelated partitions. | First repair experiment only replaces selected existing plan items with analysis/partition frozen; no add/delete/split/merge. |
| Checkpoint reuse lacked input validation. | Existing bounded tasks load by artifact name; split recovery checks item count rather than complete input identity. | Bind task artifacts and split checkpoints to input hashes, assigned IDs and versions before relying on scoped reuse. |
| Legacy export was not protected by a schema-version bump. | CLI export parses historical files through the current concrete model classes. | Dispatch readers explicitly by type/version, retain V1 readers and adapt only in memory for export. Unknown fields remain unavailable. |
| Repair was presented as an immediate cost saving. | The historical full run and active configuration have max_revisions=0. Reviewer-driven rewrite spending is currently absent. | Treat repair as a new feature with added cost. Compare corrected defects against no repair before any whole-stage-repair comparison. |
| Reviewer value and model feasibility were conflated. | With revisions disabled, findings aid triage without changing the plan. The migrated live endpoint has not been validated. | Measure valid findings and false alarms. Check live compatibility with a bounded baseline task; defer per-role routing until evidence supports it. |

Code evidence: [requirement identity and context](../src/soc_verifier/workflows/spec_to_plan/batching.py),
[plan IDs and review flow](../src/soc_verifier/workflows/spec_to_plan/batched_roles.py),
[checkpoint reuse](../src/soc_verifier/workflows/spec_to_plan/bounded.py),
[artifact loading and export](../src/soc_verifier/cli.py),
[runtime evidence binding](../src/soc_verifier/agents/runtime.py),
[domain contracts](../src/soc_verifier/domain/models.py).

## Decisions that reduce implementation rework

The source coordinate system is pinned to exact persisted text and scoped to a
source snapshot. Application-computed hashes and explicit adapter versions protect
the relationship between annotations and evidence. Source/read receipts prove
availability or location; they do not prove a claim is supported.

Task attribution, evidence binding and checkpoint validation share one task
envelope. This avoids three incompatible identity schemes. The initial envelope
does not require redesigning the application's entire domain model.

The first patch protocol is deliberately narrow: selected existing plan items,
unchanged IDs and requirement references, base/target hashes, fixed analysis/source
versions and one bounded repair round. General analysis repair requires a later
lineage and invalidation design. Missing dependency edges never establish that
other items are unaffected.

Tables have a limited support contract: tested simple layouts and clearly
identified headers. Unsupported merges and visual material remain visible gaps.
The plan does not promise full document understanding as a prerequisite for
repairing known retrieval defects.

## Alternatives considered

**Build the whole evaluation corpus first.** Rejected as a prerequisite. The
smallest useful real-workload pilot can expose failures earlier. Broader data
follows when it covers an identified blind spot.

**Require reviewed labels before any code work.** Rejected for deterministic fixes
and preparation. Required for engineering-quality acceptance. Provisional results
remain explicitly provisional.

**Make all tasks atomic and build a complete relationship graph.** Deferred. This
could reverse the existing savings from parameterized requirements and create
unsupported relations. First test specific extraction/interaction failures.

**Add automatic repair to the first release.** Deferred. Typed findings must be
useful before they drive paid correction. The existing zero-revision workflow is
the first comparison, not an imagined expensive repair baseline.

**Choose new models immediately.** Limited to a feasibility exception if the current
endpoint cannot perform a bounded task. Architecture comparisons otherwise freeze
the model; per-role optimization follows measured results.

**Commit to many repetitions and full runs in the initial pilot.** Rejected until
cost admission is known. The proposal limits the first tranche to four small
baseline/candidate workflows and a $5 aggregate ceiling. Additional repetitions,
model screens and full runs need an explicit allocation; the cap is not renewed
automatically.

## Remaining inputs and ownership

| Input | Why it matters | What can proceed without it |
| --- | --- | --- |
| User acceptance of the revised scope | The user requested plan review before implementation. | Plan review and clarification only. |
| A designated design/DV label reviewer | Needed to resolve disputed labels and judge semantic acceptance. | After scope approval: offline tooling, provenance, fixtures, deterministic tests and provisional annotations. |
| An accepted paid-evaluation budget | The proposed $5 slice limit is not yet accepted; conservative per-request reservations may constrain the run allocation. | Offline preparation and fixes after scope approval; no live evaluation. |
| Authoritative resolution of source conflicts | A reference-plan disagreement cannot be resolved by agent voting. | Preserve opposing evidence and unresolved status; do not invent behavior. |

Codex prepares implementation, fixtures and comparison reports. Each PR needs an
independent code review. A design/DV owner, who may be the user if appropriate,
owns semantic labels and acceptance. No engineer assignment or approval is assumed.

## Final council review

| Track | Result |
| --- | --- |
| Dataset relevance and evaluation | No blocking issue identified in the revised scope, label states, denominators or source-only input separation. |
| Architecture and compatibility | No blocking issue identified in contract sequencing, snapshot reuse, legacy readers or narrow patch identity. |
| Delivery and spending | No blocking issue identified. The proposed $5 tranche covers one two-packet baseline/candidate comparison only, not later PR comparisons or full-DOCX runs. |

This closes the council's planning review. User scope acceptance, a paid budget
and engineering-label review remain the distinct inputs listed above.

These decisions reduce avoidable rework; they do not establish that all future
behavior is known. The remaining uncertainties have explicit experiments and
stop conditions instead of becoming mandatory architecture.
