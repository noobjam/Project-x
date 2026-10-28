# Agent implementation roadmap

Council-reviewed plan, revised 26 October 2026. Planning baseline: 7c2f05d.
Live milestone/ticket status, authorization and next actions are maintained in
[project progress](progress.md). This file defines scope and acceptance criteria.

Deliver a better verification-plan draft for the actual Management CPU DOCX.
Use OpenTitan as supporting evaluation material. The first release improves
evidence access, reviewer findings and visibility into agent work and cost.
Broader obligation redesign, relationship maps, patterns and automatic repair
depend on measured failures that justify them.

The research comparison is preserved below; the revised scope and decision log
are in [the council review](agent-council-review.md).

## Acceptance workload and evaluation scope

| Layer | Initial input | What it establishes |
| --- | --- | --- |
| Primary workload | The local Management CPU DOCX, its existing generated artifacts and human reference plan | Whether changes help this project. Use focused, source-complete packets for iteration, then the full original DOCX for acceptance. |
| Public IP diagnostic | One pinned OpenTitan UART source package | Portable checks of extraction, source support and scenario quality. A narrow evaluation fixture adapter is enough. |
| Public integration diagnostic | One source-complete cross-IP packet, selected after checking its contributing specifications | Cross-component reasoning. USB suspend/wakeup is a candidate, not an already assembled benchmark. |
| Ingestion regressions | Actual private DOCX locally, plus small permitted or synthetic DOCX fixtures | Tables, headings, offsets, missing media and extraction behavior independently of model quality. |

Start the private packets with a table, reset behavior and a known contradiction,
retaining the definitions and cross-references needed to interpret them. Keep all
proprietary source text, annotations and outputs local and ignored by Git.

The previously inspected private reference is development and acceptance-regression
evidence, not a blind test. OpenTitan is public and may appear in model training.
Do not claim generalization from either. Additional public IPs and independent
families are later expansion, not prerequisites for the first release.

Agents receive source evidence only. Human plans, tests, coverage code and
annotations stay outside runtime retrieval. Record provenance for each label:
agent-proposed, imported reference, human-reviewed or disputed. A reference-plan
disagreement remains disputed until the source/design owner resolves its authority.

Freeze the scoring scope before looking at candidate results:

- Reviewed, in-scope obligations form the reviewed metric denominator.
- Provisional obligations are reported separately; their scores are exploratory.
- Known obligations behind missing evidence remain missed or unresolved. Unknown
  visual/table content is marked coverage unknown, not assigned an invented count.
- Ambiguous source is assessed for correct identification and evidence, not for an
  invented answer.
- Non-normative/out-of-scope exclusions require a recorded reason and authority.
  Parsing failures cannot become exclusions.

Slice recall is never presented as full-document recall. Counts of visited blocks
do not establish completeness. Human editing time is reported only when measured.

## What we borrow

| Reference | Applicable technique | Boundary |
| --- | --- | --- |
| [Spec2Plan](https://63dac.conference-program.com/presentation/?id=WIP3284&sess=sess307) | Evaluate source coverage separately; use verification techniques and integration scenarios. | Our staged workflow already exists. Its abstract does not establish reproducible performance for our workload. |
| [Arm GAIL-V](https://dvcon-proceedings.org/wp-content/uploads/DVConEU_2025_paper_169.pdf) | Separate extraction/planning/review evaluation; test reviewers with known mistakes and valid controls. | Automated judging is provisional until calibrated against engineering review. |
| [Intel formal testplanning](https://dvcon-proceedings.org/wp-content/uploads/2B3-DVCon_India_2024_Final_Paper_1423.pdf) | Assess whether planned checks can be implemented and distinguish violations. | We do not yet execute formal checkers. |
| [CorrectBench](https://arxiv.org/html/2411.08510v1) | Localize scenario defects and correction feedback. | Adopt a narrow patch contract; exhausted repairs remain unresolved. |
| [AssertLLM](https://arxiv.org/html/2402.00386v2) | Gather related evidence across sections, signals and timing information. | Fix text/table context first; unprocessed visual evidence remains visible. |
| [HAVEN](https://github.com/mcc311/haven) | Typed intermediate artifacts and deterministic handling of recurring structure. | A pattern experiment may follow; adopting its execution framework is unnecessary. |
| [OpenTitan DV methodology](https://github.com/lowRISC/opentitan/blob/master/doc/contributing/dv/methodology/README.md) | Link specifications, authored testpoints and implementations. | Reference plans require curation; block-level success does not establish SoC-level competence. |

## Design decisions fixed for the first release

1. Keep the SDK/OpenRouter runtime, three existing specialist roles and Python
   orchestration as the baseline. The number of roles is not a success criterion.
2. Keep current requirement and plan shapes unless a specific first-release
   contract needs extension. Do not introduce a universal obligation/check graph.
3. Source IDs are stable only within a pinned source snapshot. Multi-file inputs
   use document-scoped IDs. Preserve existing document hashes; record package,
   projection and adapter provenance separately.
4. Where spans are used, offsets address exact persisted SourceBlock.text in
   Unicode code points, with half-open start/end ranges. The application computes
   the text hash. Pin normalization/adapter versions; never normalize after offsets
   exist. A correct span proves location, not semantic support.
5. One task envelope carries task ID, role/stage, assigned IDs, explicit input
   artifact names/hashes and prompt/schema versions. Use it for evidence access,
   attribution and checkpoint validation. Avoid implicit latest-artifact discovery.
6. Historical readers dispatch by artifact type and declared version. Adapt legacy
   data only in memory for export; unavailable evidence stays unavailable. Unknown
   versions fail clearly. Incompatible resumes are rejected, without rewriting
   saved artifacts. Spend remains independent of domain-schema changes.
7. Initially support clear table headers and tested simple layouts. Ambiguous
   merged layouts retain warnings. Full DOCX layout understanding is separate work.
8. Automatic repair is optional. Its first form replaces existing plan items with
   source, analysis and partition frozen. Analysis additions/deletions/splits,
   scenario additions and general dependency repair are outside that experiment.

## Ticket backlog

Dependencies are implementation dependencies. See [project progress](progress.md)
for current execution status. SV-10 is a repeated evaluation activity, not a final
testing phase.

### SV-01 Freeze the real-workload pilot and evaluation contract

Priority: P0. Dependencies: none. First release: required.

Substeps: A freeze scope/provenance; B assemble source-faithful packets;
C add annotation states and scoring.

Deliver a local acceptance manifest for the original DOCX/reference/artifacts,
the baseline code/configuration and the smallest public diagnostic set above.
Use the actual DOCX ingestion path. Build only the narrow public fixture adapter
needed for the selected sources, under evaluation tooling rather than a new
general-purpose ingestion product. Freeze hashes and label versions.

Acceptance:

- Offline preparation requires no paid run or assumed availability of a DV owner.
- Runtime source inputs cannot access reference labels, authored plans or tests.
- Removing a labelled obligation from agent output, while leaving the source and
  reference inventory unchanged, lowers recall even if all remaining IDs are linked.
- Source mutations receive new expected labels; controls stay unchanged.
- Scoring separates extraction, unsupported behavior, scenario adequacy, reviewer
  false alarms and incomplete outcomes.
- Unreviewed labels and unavailable evidence cannot produce a semantic pass.

Edit points: new evals tooling/manifests; small permitted or synthetic fixtures;
ignored local corpora and result artifacts.

### SV-02 Bind agent work to input snapshots and spending

Priority: P0. Dependencies: SV-03A task/source convention.
First release: required.

Deliver the shared task envelope, exact runtime evidence references, per-attempt
attribution and a simple local task/cost report. Bind persisted outputs and split
checkpoints to input fingerprints, including assigned IDs and content, rather
than trusting a filename or item count alone.

Acceptance:

- Every attempt, tool follow-up, failed output and unsettled reservation belongs
  to exactly one task; attribution remains correct with concurrent workers.
- Billed charges and unsettled reservations reconcile separately to the ledger.
- Resume reuses work only when task inputs and versions match; stale reuse is rejected.
- Instrumentation preserves baseline request content/settings. Any behavior change
  is recorded as a separate comparison condition.
- Logs exclude source/tool text; sensitive artifacts remain local.
- User-approved compatibility companion: preserve OpenRouter reasoning metadata
  across tool follow-ups, test concurrent isolation offline, and record this as a
  separate behavior condition. Live model/provider feasibility remains SV-10A.

Edit points: agents/runtime.py, workflow task calls, bounded.py, providers/,
storage/ and cli.py.

### SV-03 Establish minimal evidence and compatibility contracts

Priority: P0. Dependencies: none for A; SV-01 provenance for B.
First release: required in its limited scope.

A is a short design/fixture step fixing the conventions above, before new schemas
are implemented. B adds only the source/task metadata and versioned readers
needed by the first release. Typed finding fields are implemented with SV-07.
Obligation atomization, check IDs and a relationship schema are deferred.

Acceptance:

- Unicode casefold expansion, repeated text, tabs and line endings cannot produce
  offsets into a different representation.
- Malformed spans, mismatched text hashes and unknown versions fail explicitly.
- Completed V1 runs still export with missing new fields marked unavailable;
  spend reads unchanged ledgers without inference.
- A mismatched prompt/schema/source-processing version cannot silently resume.
- Changes are additive where practical; no silent migration of immutable artifacts.

Edit points: domain contracts, explicit artifact loaders, runtime task interfaces,
CLI/export loading and compatibility fixtures.

### SV-04 Correct retrieval and bounded source context

Priority: P0. Dependencies: SV-03A conventions; coordinate snapshot metadata
with SV-02/03B. No dependency on SV-05 or SV-06.
First release: required.

Deliver match-centered excerpts, offsets, stable search pagination and bounded
section/neighbor access. Apply the same table-context rules in chunk prompts and
tools. Add only the metadata needed for supported layouts.

Acceptance:

- A match beyond character 1,000 is visible and maps back to exact persisted text.
- More than 12 hits are traversable without missing or repeating entries.
- A data row receives its supported header context or an explicit warning.
- Unknown references, oversized items and retrieval bounds still fail safely.
- Untrusted document text never expands tool permissions.
- Offline counterexamples pass; SV-10B checks effects on real packets.

Edit points: agents/tools.py, ingestion/docx.py and workflow batching/context.

### SV-05 Experiment with extraction coverage and interaction links

Priority: P2. Dependencies: SV-01/04 and an SV-10B result showing remaining
extraction or cross-section failures. First release: deferred.

Bounded exception admitted after the connected diagnostic: when the complete small
packet was demonstrably supplied and a model screen still misses explicit facts,
an instructions-only coverage trial may precede SV-04. It adds no extraction
schema or interaction index and must be compared before expansion.

After that prompt-only trial failed, the user approved a structured bounded-packet
trial before SV-04: extract conditions, values/constraints and exceptions with
exact source quotations; record grouped non-normative/unresolved dispositions;
compute unaccounted source text locally. Keep accounting separately versioned and
project facts into the existing analysis/plan contracts. Start opt-in with one
bounded source chunk, rejecting larger inputs before inference. No interaction
index or additional role is included. This limited scope does not complete the
full ticket or authorize full-document expansion.

Test independently reviewable behavioral obligations and a small source-linked
interaction index for identified failures. Preserve parameterized register/interrupt
families when the source supports uniform behavior. Use compact source dispositions;
do not require an LLM record or call for every source block.

Acceptance:

- Conditions, units and exceptions survive extraction; disputed behavior is unresolved.
- Representation size and calls are measured before full-document expansion.
- Improvement comes from correctly recovered behavior, not more rows.
- Missing relationship edges are unknown dependencies, not proof of independence.
- Fabricated quotations/IDs and stale accounting fail before planning. Unaccounted
  text remains visible; quoted text is never called semantically covered by code.
- Structured facts survive projection into planner inputs and offline exports.
  Interrupted execution reuses validated extraction; historical exports/spend work.

Cancel or defer expansion if it fails the targeted cases, creates unsupported
relationships or increases cost/review effort without a measured benefit.

Edit points: analyst instructions, batched analysis and small typed local indexes.

### SV-06 Evaluate check adequacy before expanding planner schemas

Priority: P2. Dependencies: SV-01 and SV-10B evidence of weak scenarios.
SV-05 is required only if the experiment uses its new relationships.
First release: deferred beyond evaluating existing fields.

Assess the existing preconditions, stimulus and expected-results fields against
an observation and discriminating pass/fail criterion. If needed, trial a few
source-conditioned reset, boundary or ordering suggestions before building a library.

Acceptance:

- An actionable scenario can distinguish a relevant violation; unknown
  observability or environment capabilities stay explicit.
- No pattern invents timing, addresses, APIs or hardware behavior.
- Duplicates and extra prose do not improve adequacy scores.
- Only a demonstrated failure of the existing representation justifies new check IDs.

Cancel or defer a pattern library if it adds rows without better adjudicated checks.

Edit points: planner instructions/evaluation first; schema/pattern modules only
after the experiment supports them.

### SV-07 Add typed review findings on existing plans

Priority: P0. Dependencies: SV-03B, current analysis/plan artifacts.
SV-04 supplies improved retrieval but no SV-05/06 redesign is required.
First release: required.

Retain severity, target and description. Add defect kind, affected source,
requirement and plan-item references, supporting evidence and an actionable
repair request or unresolved reason. A missing obligation may cite source evidence
without an existing requirement or scenario ID. Feed bounded local findings into
global review, with retrieval for detail.

Acceptance:

- Invalid references fail locally; global defects do not require invented IDs.
- Known timing, omission, unsupported-result and weak-check defects are assessed
  alongside valid controls; detection and false alarms are reported.
- Specification contradictions remain owner-resolution issues.
- Tool-read receipts and schema validity are never treated as proof of support.
- With revisions disabled, measure valid triage findings and false alarms; do not
  claim the unchanged plan itself improved merely because findings increased.

Edit points: domain finding contract, reviewer instructions, reviewing.py and
batched_roles.py.

### SV-08 Trial one bounded plan-only repair

Priority: P2. Dependencies: SV-02/03/07, usable repairable findings and an
SV-10 decision to test repair. First release: deferred.

Treat existing fully qualified plan IDs as opaque handles within a frozen source,
analysis and partition. Replace only an explicitly selected set of existing items;
retain IDs and requirement_ids. Initially forbid add/delete/split/merge/repartition.

Require base-plan hash, target-item hashes, source/analysis references and task
versions. Reject stale patches, assemble a new immutable plan revision, validate
globally and review affected local scopes plus integration behavior.

Acceptance:

- Unaffected serialized item hashes remain unchanged; no unrelated planning calls.
- Repair checkpoints match exact inputs; interruption preserves charges and outputs.
- Unknown dependencies widen review rather than silently skipping it.
- Findings needing new obligations/scenarios remain unresolved or require broader work.
- One bounded repair round corrects assessed defects without new critical defects;
  exhaustion never becomes success.

Current max_revisions is zero. This adds a capability and cost; it does not save
existing semantic-repair calls. Compare first with no repair. Compare with bounded
whole-stage repair only if that additional experiment is justified and funded.

Edit points: a narrow workflow patch protocol, persistence and repair tests.
General analysis repair needs a separate identity/lineage design.

### SV-09 Produce a useful review view

Priority: P0. Dependencies: SV-02/03/07; no SV-05/06 dependency.
First release: required.

Extend the existing CLI/Excel view to connect scenarios, requirements, available
source evidence, findings and task costs. Show source contradictions, unavailable
visual/table information and unresolved checks. A dashboard is not a prerequisite.

Acceptance:

- An engineer can follow a finding to its exact available evidence and affected item.
- Source linkage is not called semantic coverage; absent gold labels mean unknown
  recall, not an invented percentage.
- Legacy export remains usable and new unknown fields remain visibly unavailable.
- Automated output is a draft, never a claim of execution or human approval.

Edit points: export/xlsx.py, cli.py and the export-facing view model.

### SV-10 Run comparisons throughout delivery

Priority: P0. Dependencies vary by step. First release: required.

A: freeze baseline before behavior changes; execute a bounded slice baseline once
SV-01 and sufficient SV-02 accounting exist. Preserve baseline code/configuration
so comparisons remain possible from an isolated checkout. Offline fixes need not
wait for a new full-spec paid run.

B: compare each meaningful candidate with its parent and the frozen baseline,
using unchanged cases, model/provider, generation settings and declared limits.
Use offline checks first; group inseparable changes as an explicit condition.
Prior baseline outputs may be reused only when all effective inputs match.

The user-requested KB diagnostic adds a bounded connector before the broader
SV-04 source-retrieval work: versioned public-entry catalog, frozen per-run
snapshot, specialist search/read tools and role/task access records. Default to
approved entries; proposed material requires explicit trial opt-in. Validate
snapshot changes, retrieval limits, source/knowledge separation and legacy reads
offline before generating a source-only/KB-connected pair on the separate
Management CPU packet. Keep human reference answers outside retrieval. Report
actual reads separately from correct application; this does not complete SV-04,
SV-06 or semantic acceptance. Preserve the existing task budget across failures.

C: test repair only after SV-08 is admitted. Measure corrected defects, introduced
defects and added cost against no repair. A single-agent/two-stage comparison is
optional when testing stage value, not a prerequisite for fixing retrieval.

D: after useful slice results, run the original full Management CPU DOCX as an
end-to-end baseline/candidate acceptance comparison. Report known regression cases,
input limitations, unresolved source conflicts, completion, costs and draft output.
Public-IP scores cannot substitute for this result.

Acceptance:

- Failed, malformed, interrupted and budget-exhausted runs remain in results.
- Judge reviewed and provisional labels separately; editing time is measured or
  explicitly not measured.
- For quality acceptance: improve the targeted adjudicated defect without a new
  critical miss/unsupported behavior on the reviewed sample. Conflicting or noisy
  results remain inconclusive; do not hide a quality loss in an aggregate score.
- A cheaper candidate must preserve the declared quality gates; a more expensive
  one needs an explicit quality/effort tradeoff. No universal dollar-per-spec target
  has been selected.
- Without reviewed labels, report technical readiness and pending semantic
  acceptance. Public and private development cases do not prove generalization.

Edit points: evals comparison runner, result schemas and local reports.

### SV-11 Check model feasibility early and route later

Priority: P2 for routing. Early compatibility check is part of SV-10A.
Dependencies: usable evaluation evidence; routing requires an accepted architecture.
First release: shared model remains default.

Use a bounded baseline task to verify current tools, structured output, limits,
reasoning-metadata round trips where applicable, and endpoint behavior. If it cannot complete or gives unusable results, investigate
configuration/provider errors first. Any alternative-model screen is a separately
declared, budgeted condition; do not silently expand experiments.

After architecture evidence exists, compare a small candidate set and add explicit
per-role settings only where they show value. Preserve pinned model/endpoint
selection, configured data handling and no silent fallback.

Acceptance:

- Every role/follow-up obeys global call/cost limits and recorded routing.
- Resume preserves pricing/settings. Unsupported tiered prices still fail safely
  unless a separate tested reservation bound is implemented.
- Role routing improves adjudicated quality, cost or effort against a shared-model
  baseline. Leaderboard position or token price alone does not select a model.

Edit points: evaluation configurations first; settings/runtime/provider changes later.

## Delivery sequence and decision gates

| Stage | Work | Exit decision |
| --- | --- | --- |
| Preparation | SV-01A/B/C and SV-03A conventions | Case provenance, scoring states and contract examples are reviewable. Engineering-label ownership and paid budget remain explicit inputs. |
| Baseline foundation | SV-02 and minimal SV-03B | Accounting reconciles, snapshots are bound, legacy reads work. SV-10A can run under an accepted cap. |
| First behavior slice | SV-04, with SV-10B | Retrieval regressions pass; accept, revise or revert based on the targeted packet evidence. |
| Review slice | SV-07 plus minimal SV-09, with SV-10B | Findings help triage without unacceptable false alarms; source evidence and cost are inspectable. |
| First release candidate | SV-10D on the actual DOCX | Technical outcome and engineering acceptance are reported separately. Remaining conflicts/visual gaps stay visible. |
| Conditional follow-ups | SV-05, SV-06, SV-08 or SV-11 | Start only for a measured remaining problem and a testable improvement hypothesis. |

Use focused feature branches off the migration baseline, small PRs and review before
merge. Recheck local/remote state before opening PRs; preserve the migration
baseline rather than accidentally building from an older remote commit.

Normal tests stay offline. Run required Ruff, mypy, pytest and build checks for
code changes. Update the smallest affected docs and bump prompt/persisted schema
versions when their behavior changes.

## Spend proposal and execution boundaries

Proposed initial pilot ceiling: **$5 total**. Record acceptance and remaining
allocation in [project progress](progress.md) before paid execution. This is an
experiment limit, not a target price for a complete specification. Preserve the
current $2 maximum per run, and preallocate individual run ceilings whose sum is
no greater than the pilot limit. The gateway's conservative reservation must fit
each allocation before inference starts.

This tranche funds at most one baseline/candidate comparison across two packets,
not every behavior PR. Start with at most four small workflows: one Management CPU
packet and one supporting/control packet, each under baseline and candidate. The baseline task
also checks live compatibility. These are diagnostic comparisons, not statistical
proof. All follow-ups, failures and corrections consume the allocation. Repeated
comparisons and model screens do not silently renew the cap or workflow allowance.

If the allowance cannot fit a meaningful experiment, return a budget-feasibility
result and reduce scope or propose a revised allocation. Full-DOCX paired runs
require their own declared allocation within an accepted total budget. They are
not silently added to the $5 slice pilot. Unknown charges remain reserved.

Codex prepares code, fixtures, candidate annotations and reports. A designated
design/DV reviewer approves engineering labels and acceptance judgments; track
that assignment in [project progress](progress.md). Missing label review blocks semantic claims,
not reversible offline preparation and deterministic fixes.

The first implementation milestone is the preparation PR: the real-workload
manifest, pilot/annotation format, source-only fixtures and SV-03A contract examples.
Use [project progress](progress.md) and the latest user instruction to determine
the next authorized action; this roadmap alone does not authorize paid execution.
Simulation/formal execution, Booley/JEV, automatic diagram
interpretation, fine-tuning and a larger agent team remain follow-on work.
