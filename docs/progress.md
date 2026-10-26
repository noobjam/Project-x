# Project progress

Last updated: 2026-10-26.

This is the live status and session handoff. Ticket scope and acceptance criteria
are in [the roadmap](agent-roadmap.md); design rationale is in
[the council review](agent-council-review.md). Read [AGENTS.md](../AGENTS.md) for the
required session and milestone update workflow.

## Current state

- **Phase:** council planning and session continuity documentation are complete.
  Application implementation of the revised backlog has not started.
- **Current working plan:** a smaller first release focused on source retrieval,
  structured findings, agent task/cost reporting and reviewable output, evaluated
  against the real Management CPU DOCX.
- **Implemented baseline:** OpenAI Agents SDK analyst/planner/reviewer agents,
  bounded evidence tools, OpenRouter transport, Python orchestration, immutable
  artifacts and Excel export. LangGraph/LangChain were removed.
- **Next application milestone:** preparation, starting with SV-01A and SV-03A;
  then source-faithful pilot fixtures and annotation/scoring states (SV-01B/C).
- **No new paid evaluation:** the migrated runtime has not yet had a paid live
  engineering evaluation. Quality and savings remain unmeasured.

## Repository snapshot

Checked on 2026-10-26:

- Local branch: main. Publication checkpoint: 2bb4293, which includes the SDK
  migration and all four roadmap/continuity documents.
- Migration commit: 5d15c10; preserved pre-migration prototype: 10f5bad.
- Push destination: https://github.com/noobjam/Project-x.git. The push advanced
  GitHub main from 35e0259 to 2bb4293; git ls-remote verified the matching SHA and
  the working tree was clean. This entry records that publication checkpoint;
  subsequent status-only commits may advance the tip.
- Roadmap, council review and session-continuity files are committed and published.
  No implementation branch or external ticket links have been created for the
  revised backlog.

Recheck Git state on resume; this snapshot is not a permanent assertion.

## Milestone status

| Milestone | Status | Evidence and remaining work |
| --- | --- | --- |
| SDK migration | done | Merged at 7c2f05d and published to GitHub in the push through 2bb4293. Last recorded validation: 112 tests passed, Ruff, mypy and build passed. These checks were reported in the migration session, not rerun for publication. |
| Research council and plan revision | done | Three tracks reviewed dataset relevance, architecture and delivery/cost. Final review found no blocking planning issue; see the council review. This is not semantic validation of agent outputs. |
| Session continuity documentation | done | Root instructions and progress tracker created. All 40 local links/anchors, 11 ticket entries and whitespace checks passed. Published with the roadmap/council review at 2bb4293. |
| Preparation | planned | SV-01A/B/C and SV-03A. No application code or pilot fixtures implemented yet. |
| Baseline foundation | planned | SV-02 and minimal SV-03B. Must establish task attribution, input binding and legacy reads. |
| Retrieval and review release | planned | SV-04, SV-07 and SV-09, with SV-10 comparisons during delivery. |
| Full real-workload acceptance | planned | SV-10D after useful slice evidence, declared funding and engineering review. |

## Ticket status

All scopes below link to their acceptance criteria. No implementation ticket is
complete merely because its plan exists.

| Ticket | Status | Current position and next step |
| --- | --- | --- |
| [SV-01](agent-roadmap.md#sv-01-freeze-the-real-workload-pilot-and-evaluation-contract) | planned | Start A: local-only source/reference/baseline manifest. Then B/C: source-complete packets, annotation states and scoring. |
| [SV-02](agent-roadmap.md#sv-02-bind-agent-work-to-input-snapshots-and-spending) | planned | Implement task envelope and spending attribution after SV-03A conventions. |
| [SV-03](agent-roadmap.md#sv-03-establish-minimal-evidence-and-compatibility-contracts) | planned | Start A alongside SV-01: source/span/task conventions and contract examples. B adds minimal versioned readers/metadata later. |
| [SV-04](agent-roadmap.md#sv-04-correct-retrieval-and-bounded-source-context) | planned | Fix matching excerpts, pagination and bounded table/neighbor context after minimal contracts. |
| [SV-05](agent-roadmap.md#sv-05-experiment-with-extraction-coverage-and-interaction-links) | deferred | Start only if measured extraction/cross-section failures justify it. |
| [SV-06](agent-roadmap.md#sv-06-evaluate-check-adequacy-before-expanding-planner-schemas) | deferred | Evaluate existing scenario fields first; patterns/schema expansion require evidence. |
| [SV-07](agent-roadmap.md#sv-07-add-typed-review-findings-on-existing-plans) | planned | Typed source/requirement/item findings and local-to-global review; no graph/pattern prerequisite. |
| [SV-08](agent-roadmap.md#sv-08-trial-one-bounded-plan-only-repair) | deferred | Optional existing-item replacement against frozen analysis/partition after usable findings. |
| [SV-09](agent-roadmap.md#sv-09-produce-a-useful-review-view) | planned | Extend CLI/Excel with findings, evidence, limitations and task costs. |
| [SV-10](agent-roadmap.md#sv-10-run-comparisons-throughout-delivery) | planned | A baseline, B incremental comparisons, C optional repair experiment, D full-DOCX acceptance. Preparation may proceed offline. |
| [SV-11](agent-roadmap.md#sv-11-check-model-feasibility-early-and-route-later) | deferred | A bounded current-endpoint feasibility check belongs to SV-10A; per-role routing is later. |

## Decisions and execution boundaries

- The user challenged the missing GitHub commits; publication to the confirmed
  repository is complete. This does not start application implementation or paid
  evaluation. On a later
  instruction to continue implementation, start the next eligible offline action;
  do not require the user to restate the plan or repeat settled decisions.
- The council-reviewed roadmap is the current working proposal. Record any user
  scope acceptance or change here when it is given; council agreement alone is
  not user acceptance or engineering approval.
- The new paid pilot's **$5 total ceiling is proposed, not accepted**. It covers at
  most one baseline/candidate comparison across two small packets, not all PRs or
  full-document runs. Proposed per-run allocations must fit conservative reservations
  and sum to the accepted ceiling. Earlier prototype testing is already completed;
  it does not establish approval for this new pilot tranche.
- No design/DV label reviewer has been assigned. Provisional annotations are
  allowed; semantic acceptance requires reviewed labels. This does not block
  offline preparation or deterministic fixes once implementation is requested.
- Private reference material already inspected is development/acceptance-regression
  evidence, not blind gold. Missing visual evidence remains a visible limitation.
- Revisions are currently disabled in the recorded run configuration. Optional
  repair adds capability and cost; do not claim it saves existing repair spending.
- Model selection, Booley/JEV, execution tools, automatic diagram interpretation
  and broader agent teams remain deferred according to the roadmap.

## Next moves

1. **When implementation is requested, start SV-01A and SV-03A.** Recheck the local
   published main and any later working-tree changes; preserve them. Use a focused
   feature branch such as feat/agent-evaluation. Verify local/remote state before
   remote PR work without losing the migration.
2. **Freeze provenance before behavior changes.** Record local source/reference
   hashes, known artifact provenance and baseline code/prompt/schema/settings.
   Keep private material and answers under ignored local artifacts. Prepare source
   identity, span-coordinate and task-envelope examples.
3. **Build the smallest offline pilot.** Use actual DOCX ingestion for a table,
   reset and contradiction packet with necessary context. Add one pinned UART
   fixture and select one source-complete integration packet. Keep labels outside
   agent retrieval and mark their review state.
4. **Review the preparation PR and checkpoint progress.** Record actual checks,
   completed substeps and the next concrete change. Proceed to SV-02/minimal
   SV-03B; do not jump to a full graph or general repair engine.
5. **Before paid evaluation, resolve only the applicable missing inputs.** Confirm
   the pilot allocation and record authorization. Identify the engineering reviewer
   before making semantic-acceptance claims. A proposed budget does not authorize
   spending; a missing label reviewer does not block explicitly authorized
   exploratory runs whose conclusions remain provisional.

## Validation and result references

- Migration: last recorded 112 passing tests and Ruff/mypy/build success. See
  [architecture validation](architecture.md#validation-and-next-capabilities).
  This establishes offline software behavior, not current provider compatibility.
- Historical pre-migration full run: 39b3204e-9398-413a-97b8-aa80908f4e40;
  127 settled calls, $1.145865325, 95 plan items and 157 findings. This is context,
  not a controlled migrated-runtime baseline or proof of engineering quality.
- Safe local artifact references: artifacts/runs/39b3204e-9398-413a-97b8-aa80908f4e40/
  and artifacts/research-council-2026-10-26.html. These are ignored, machine-local
  artifacts and may be absent in another checkout; do not copy their private content
  into tracked documents.
- Current documentation validation: inline Python checks passed for 40 local
  links/anchors, all 11 ticket status entries and whitespace; git diff --check
  also passed. The inline check covered the untracked documents explicitly.
  No code tests or paid inference were run for this documentation-only change.
- Publication: all three previously unpublished commits and four documentation
  files were checked for private paths and credential patterns before the push.
  git ls-remote confirmed GitHub main at 2bb4293 and git status showed a clean,
  synchronized working tree at that checkpoint. No force push was used.

## Milestone history

### 2026-10-26 SDK migration and architecture planning

- Migrated to SDK agents with bounded evidence tools and merged locally at 7c2f05d.
- Completed the research council, then a second review of the implementation plan.
- Re-centered acceptance on the Management CPU DOCX, narrowed the first release and
  made later architecture work conditional. Preserved ticket IDs SV-01 through SV-11.
- Application implementation of those tickets remains unstarted; next milestone
  is offline preparation. The new pilot budget and label owner remain unresolved.

### 2026-10-26 Session continuity setup

- Added root instructions and this progress tracker; moved live status out of
  roadmap prose and linked the historical council review back to this file.
- Validation: 40 local links/anchors, all 11 ticket entries and whitespace checks
  passed. No runtime changes, code tests or paid runs. Files were initially local;
  their publication is recorded below.
- Next action when implementation is requested: SV-01A/SV-03A preparation on a
  focused feature branch, followed by the smallest offline pilot.

### 2026-10-26 GitHub publication

- Confirmed fetch and push destination: noobjam/Project-x. GitHub had remained at
  the October 11 commit because the migration was merged locally without a push.
- Committed the four roadmap/continuity documents as 2bb4293 and pushed main,
  including the three existing migration/prototype commits. Verified the remote
  SHA directly and confirmed a clean synchronized working tree.
- Added an explicit remote-verification rule to AGENTS.md and updated this handoff.
- Next application ticket remains SV-01A alongside SV-03A. No paid runs were made.

<!-- At each milestone/handoff, update the current sections and append an entry:
Date and milestone; ticket/substep status; changes and safe evidence links;
checks actually run and outcomes; decisions/authorization; blockers and scope;
ordered next action. Include commit/PR references only when they exist.
-->
