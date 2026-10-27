# Project progress

Last updated: 2026-10-27.

This is the live status and session handoff. Ticket scope and acceptance criteria
are in [the roadmap](agent-roadmap.md); design rationale is in
[the council review](agent-council-review.md). Local sessions also use an ignored
AGENTS.md instruction file; it is intentionally absent from the published tree.

## Current state

- **Phase:** SV-02/minimal SV-03B implementation is technically complete on
  feat/task-accounting in [PR #3](https://github.com/noobjam/Project-x/pull/3). It adds exact task/input bindings,
  per-call spending attribution, compatible readers and OpenRouter reasoning replay.
  Evaluation preparation remains merged through PR #2; engineering acceptance is pending.
- **Current working plan:** a smaller first release focused on source retrieval,
  structured findings, agent task/cost reporting and reviewable output, evaluated
  against the real Management CPU DOCX.
- **Implemented baseline:** OpenAI Agents SDK analyst/planner/reviewer agents,
  bounded evidence tools, OpenRouter transport, Python orchestration, immutable
  artifacts and Excel export. LangGraph/LangChain were removed.
- **Active milestone:** review PR #3. Implementation 373ed26 is published; all
  push/PR CI checks passed on Python 3.12 and 3.13. Local validation passed:
  202 offline tests, Ruff, mypy and source/wheel build.
  The next implementation after merge is SV-04 retrieval and bounded source context.
- **No new paid evaluation:** the migrated runtime has not yet had a paid live
  engineering evaluation. Quality and savings remain unmeasured.
- **Local instructions:** AGENTS.md stays on the Mac and is excluded from Git.
  The roadmap, council review and this progress tracker remain shared documents.

## Repository snapshot

Checked on 2026-10-27:

- Local branch: feat/task-accounting, based on main at 46e0b06. Implementation
  commit 373ed26 is published and directly verified on origin. This documentation
  handoff advances the feature branch. AGENTS.md remains local-only and ignored.
- Migration commit: 5d15c10; preserved pre-migration prototype: 10f5bad.
- Push destination: https://github.com/noobjam/Project-x.git. Main contains PR #2
  at 927f5fb plus its handoff. Frozen baseline 6c819bf and pilot 3e5d6da are unchanged.
- Roadmap, council review and progress are published. AGENTS.md was removed from
  tracking at 82df541; its local copy remains ignored. Earlier history is unchanged.

Recheck Git state on resume; this snapshot is not a permanent assertion.

## Milestone status

| Milestone | Status | Evidence and remaining work |
| --- | --- | --- |
| SDK migration | done | Merged at 7c2f05d and published to GitHub in the push through 2bb4293. Last recorded validation: 112 tests passed, Ruff, mypy and build passed. These checks were reported in the migration session, not rerun for publication. |
| Research council and plan revision | done | Three tracks reviewed dataset relevance, architecture and delivery/cost. Final review found no blocking planning issue; see the council review. This is not semantic validation of agent outputs. |
| Session continuity documentation | done | Local agent instructions and shared progress tracker created. Initial documentation checks passed. AGENTS.md is now local-only; roadmap, council review and progress remain published. |
| Preparation | done | SV-01A/SV-03A merged in PR #1; SV-01B/C merged in PR #2 at 927f5fb. Five local packets, 37 provisional/disputed labels, scoring controls and the frozen inventory are technically complete. Context/label engineering review and paid evaluation remain separate. |
| Baseline foundation | in_review | SV-02/minimal SV-03B implemented with exact snapshots, separate invocation/call records, task spending, strict resume, legacy reads and reasoning replay. Local checks pass; PR review/merge pending. |
| Retrieval and review release | planned | SV-04, SV-07 and SV-09, with SV-10 comparisons during delivery. |
| Full real-workload acceptance | planned | SV-10D after useful slice evidence, declared funding and engineering review. |

## Ticket status

All scopes below link to their acceptance criteria. No implementation ticket is
complete merely because its plan exists.

| Ticket | Status | Current position and next step |
| --- | --- | --- |
| [SV-01](agent-roadmap.md#sv-01-freeze-the-real-workload-pilot-and-evaluation-contract) | done | A: merged in PR #1. B/C: merged in PR #2 with five verified packets, 37 provisional/disputed labels, scoring controls and a frozen inventory. Technical preparation is complete; engineering-quality acceptance is pending. |
| [SV-02](agent-roadmap.md#sv-02-bind-agent-work-to-input-snapshots-and-spending) | in_review | Task/input bindings, atomic completion receipts, per-call attribution and local spending report implemented on feat/task-accounting; review/merge pending. |
| [SV-03](agent-roadmap.md#sv-03-establish-minimal-evidence-and-compatibility-contracts) | in_review | A merged in PR #1. Minimal B task/run versions, exact input references, stale-resume rejection and compatible legacy readers implemented; review/merge pending. Typed findings stay in SV-07. |
| [SV-04](agent-roadmap.md#sv-04-correct-retrieval-and-bounded-source-context) | planned | Fix matching excerpts, pagination and bounded table/neighbor context after minimal contracts. |
| [SV-05](agent-roadmap.md#sv-05-experiment-with-extraction-coverage-and-interaction-links) | deferred | Start only if measured extraction/cross-section failures justify it. |
| [SV-06](agent-roadmap.md#sv-06-evaluate-check-adequacy-before-expanding-planner-schemas) | deferred | Evaluate existing scenario fields first; patterns/schema expansion require evidence. |
| [SV-07](agent-roadmap.md#sv-07-add-typed-review-findings-on-existing-plans) | planned | Typed source/requirement/item findings and local-to-global review; no graph/pattern prerequisite. |
| [SV-08](agent-roadmap.md#sv-08-trial-one-bounded-plan-only-repair) | deferred | Optional existing-item replacement against frozen analysis/partition after usable findings. |
| [SV-09](agent-roadmap.md#sv-09-produce-a-useful-review-view) | planned | Extend CLI/Excel with findings, evidence, limitations and task costs. |
| [SV-10](agent-roadmap.md#sv-10-run-comparisons-throughout-delivery) | planned | A baseline, B incremental comparisons, C optional repair experiment, D full-DOCX acceptance. Preparation may proceed offline. |
| [SV-11](agent-roadmap.md#sv-11-check-model-feasibility-early-and-route-later) | deferred | A bounded current-endpoint feasibility check belongs to SV-10A; per-role routing is later. |

## Decisions and execution boundaries

- On 2026-10-27 the user approved SV-02/minimal SV-03B and the OpenRouter
  compatibility fix after the best-practices assessment. Implement offline on
  feat/task-accounting and publish a reviewable PR; no paid inference or merge.
  Preserve reasoning metadata across tool follow-ups. Resume must reject changed
  output ceilings as changed behavior; worker scheduling remains adjustable.

- On 2026-10-27 the user requested merging PR #2 if checks were clear, and asked
  for the next move. Final review found no blocking issue; all CI checks passed
  on exact head 1cd0040. Merged with a merge commit to retain frozen provenance.
  This request completes the merge/handoff; it does not start SV-02 implementation
  or authorize paid evaluation.
- On 2026-10-27 the user said “next” after the merge handoff named SV-01B/C.
  Proceed with that offline slice, validation and a reviewable feature PR. Paid
  evaluation and merging this new PR are not included in that instruction.
- User preference: never publish AGENTS.md. Preserve its local copy and ignore
  case variants of the filename. This correction removes the current tracked file;
  the earlier commits still contain their historical copies.
- On 2026-10-27 the user said “alright lets go for it” after the offline preparation
  scope was stated. Proceed with SV-01A/SV-03A, validation and a reviewable feature
  PR. This does not approve the proposed paid pilot or merging before review.
- Later on 2026-10-27 the user requested the merge. Final code/review-state checks
  found no blocking issue and CI passed on the exact PR head, 514d0b0. PR #1 was
  merged with a merge commit to preserve the frozen baseline revision. This does
  not authorize paid evaluation or start SV-01B/C implementation.
- The earlier missing GitHub commits are published to the confirmed repository.
  The current instruction authorizes the offline preparation slice above; paid
  evaluation remains a separate decision.
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
  the authorized offline preparation or deterministic fixes.
- Private reference material already inspected is development/acceptance-regression
  evidence, not blind gold. Missing visual evidence remains a visible limitation.
- Revisions are currently disabled in the recorded run configuration. Optional
  repair adds capability and cost; do not claim it saves existing repair spending.
- Model selection, Booley/JEV, execution tools, automatic diagram interpretation
  and broader agent teams remain deferred according to the roadmap.

## Next moves

1. **Review SV-02/minimal SV-03B in PR #3.** Implementation 373ed26 is on GitHub
   and all four push/PR CI checks passed. Review/merge when authorized. Inspect task bindings, split
   recovery, ledger reconciliation and the reasoning compatibility adapter together.
2. **After merge, implement SV-04 on a new branch.** Fix matching search excerpts,
   pagination and bounded table/neighbor evidence against the existing task snapshots.
   Preserve both frozen evaluation inventories; do not expand roles or general repair.
3. **Before paid SV-10A evaluation, resolve its allocation and authorization.** The
   proposed $5 tranche is still unapproved. Check the selected endpoint's tools,
   structured output and reasoning round trips where applicable before comparisons.
   Record reasoning replay as a separate behavior condition. Identify an engineering
   reviewer before semantic-acceptance claims; offline work can continue independently.

## Validation and result references

- SV-02/minimal SV-03B: 202 offline tests passed. The preceding 201-test coverage
  run measured 90% aggregate coverage; the final test adds rejection of ambiguous
  reasoning history before another paid request. Ruff check/format, strict mypy and
  source/wheel builds passed. Twenty-four existing local documentation links/anchors
  resolve; built packages include new runtime modules and exclude private artifacts,
  documents, credentials and AGENTS.md. GitHub push/PR CI passed on both Python
  versions at implementation 373ed26, and its remote SHA was directly verified.
- New regressions cover concurrent task/call attribution and reasoning isolation,
  billed versus unsettled charges across restart, exact artifact revision selection,
  source/prompt/schema/processing/config changes, split-child identities, atomic
  completion recovery, unknown versions and credential-free legacy reporting/export.
  Prompts and domain schemas are unchanged. Reasoning replay is a separately versioned
  behavior change, not proof of live endpoint compatibility, quality or savings.
  No paid inference was performed; private evaluation inventories were not modified.

- SV-01B/C current checks: 175 offline tests passed (90% aggregate coverage),
  Ruff check/format, strict mypy and source/wheel builds passed. Twenty-four local
  documentation links/anchors resolve. Distribution inspection confirms evaluation
  modules are included while private inputs, artifacts and AGENTS.md are excluded.
  GitHub push/PR CI passed on Python 3.12 and 3.13 for implementation commit 3e5d6da
  and final PR head 1cd0040. The merge session checked these results; it did not
  repeat the local code suite.
  No paid calls were made. The explicit public-source acquisition used GitHub only.
- Frozen pilot: artifacts/evaluations/pilot-2026-10-27/. freeze-pilot and verify-pilot
  passed, pinning 22 files to clean preparation commit 3e5d6da. It contains three
  private DOCX projections
  (table/reset/conflict) and two OpenTitan projections (UART RX and USB handoff).
  The public recipe pins revision d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06 and nine
  source/license files. Original source text and labels stay in ignored artifacts.
- Packet block counts: table 18, reset 41, conflict 17, UART 226 and USB 310. These
  are adapter-dependent counts with overlapping private context, not coverage.
  All 37 labels were validated against exact source spans: 35 agent_proposed and
  2 disputed. There are no human-reviewed labels, model outputs or quality scores.
  One known obligation retains unavailable supporting detail; missing visual
  content stays coverage unknown rather than receiving invented obligations.
- New scoring regressions verify fixed denominators under output deletion,
  independently versioned labels for source mutation, unchanged controls, stale
  evidence rejection, scenario/support separation, reviewer false alarms and
  incomplete outcomes. Synthetic reviewed states exercise software gates only.
- Original preparation slice (PR #1): 130 offline tests passed (91% aggregate
  coverage), Ruff check/format, strict mypy and source/wheel build passed on
  Python 3.12.7. Twenty-one local documentation links resolve. Built distributions
  include the evaluation tooling and exclude private inputs, artifacts and local
  instructions. GitHub CI also passed on Python 3.12 and 3.13 for implementation
  commit 6c819bf and final PR head 514d0b0. The merge session verified those results;
  it did not rerun the local software suite. No model calls were made.
- SV-01A local bundle: artifacts/evaluations/management-cpu-baseline/. Freeze and
  verify --check-originals both passed. Ten files are pinned to code 6c819bf,
  prompt version 5, unchanged domain schemas and allowlisted configuration.
  Fresh DOCX ingestion produced 6,121 blocks and retained 5 extraction warnings.
  Only source/specification.json is the runtime input; the workbook and historical
  outputs are separate reference material. Semantic acceptance remains pending.
- SV-03A: [evidence/task conventions](evaluation-contracts.md) and synthetic
  tests/fixtures/evaluation/ examples cover document/block identity, exact Unicode
  spans and canonical task fingerprints. They do not implement SV-02/03B runtime
  metadata, compatibility readers or new resume behavior.
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
- Original session-continuity validation: inline Python checks passed for 40 local
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

### 2026-10-26 Keep agent instructions local

- At the user's request, removed AGENTS.md from tracking while retaining the local
  file and added a case-insensitive filename pattern to .gitignore.
- Removed the shared progress document's link to the untracked file. The roadmap,
  council review and progress remain shared; application code is unchanged.
- Historical commits are unchanged. The correction removes the file from the
  current branch, not from Git history.
- Validation: local file exists, Git index excludes it, filename case variants are
  ignored, shared document links resolve without linking to it, and staged diff
  whitespace checks passed. No code tests or inference were needed.
- Next application ticket remains SV-01A alongside SV-03A; no paid runs are needed.

### 2026-10-27 SV-01A/SV-03A offline preparation slice

- User approved this offline implementation slice. Added freeze/verify tooling in
  src/soc_verifier/evaluation/, usage/scope in evals/README.md and source/span/task
  conventions with synthetic fixtures. Existing runtime behavior is unchanged.
- Published implementation commit 6c819bf on feat/agent-evaluation and opened
  [PR #1](https://github.com/noobjam/Project-x/pull/1). Direct remote verification
  confirmed the feature commit and unchanged main. Review/merge remain pending.
- Froze the real DOCX, human workbook and historical artifacts locally against
  that clean commit; verification against originals passed. Private content and
  AGENTS.md remain ignored and are absent from the published change.
- Validation: 130 tests, Ruff check/format, mypy, source/wheel build, distribution
  privacy checks and local links passed. No paid inference or semantic approval.
- SV-01A/SV-03A are technically complete and in review; parent tickets stay
  in_progress. Next: review this PR, then SV-01B/C source packets, annotation states
  and scoring. Engineering label ownership and the paid pilot remain unresolved.

### 2026-10-27 Merge the preparation slice

- User requested merging PR #1. Final review found no blocking issues or pending
  review comments; all four push/PR CI checks passed on head 514d0b0, covering
  Python 3.12 and 3.13. Engineering-quality evaluation remains pending.
- Merged on GitHub at ec4b6c1 and fast-forwarded local main. The merge retains
  6c819bf, which the ignored local snapshot uses for code provenance.
- Updated this handoff to mark SV-01A/SV-03A done. Parent tickets and preparation
  remain in_progress because SV-01B/C and SV-03B are not implemented.
- Only progress documentation changed in the merge session. Fifteen progress
  links/anchors and whitespace checks passed; all 11 parent tickets remain tracked.
  Confirmed AGENTS.md is local-only and the baseline commit remains in history.
  No paid calls or repeat local code tests. Next implementation ticket: SV-01B/C
  source packets, annotation states and scoring.

### 2026-10-27 SV-01B/C source packets and evaluation scoring

- User requested the next ticket. Implemented offline private/public source packet
  preparation, label states and evidence checks, explicit-judgment scoring and a
  frozen pilot inventory on feat/evaluation-packets. Agent runtime behavior,
  prompts and application domain schemas are unchanged.
- Prepared table/reset/conflict packets from fresh ingestion of the frozen DOCX
  plus pinned OpenTitan UART RX and USB/pinmux/power-manager handoff packets.
  The local corpus has 35 proposed labels and two disputed alternatives. It has
  no reviewed engineering labels, completed model runs or measured quality result.
- Committed implementation as 3e5d6da; froze/verified 22 pilot files against that
  clean commit. Published the feature branch, directly verified its remote SHA,
  and opened [PR #2](https://github.com/noobjam/Project-x/pull/2). Main stays at
  4582f8e; PR review/merge is pending.
- Validation: 175 offline tests, Ruff check/format, strict mypy and source/wheel
  build passed; local links and distribution privacy checks passed. All five real
  packets and their exact evidence spans validate. GitHub CI passed on both Python
  versions for 3e5d6da. No paid calls. Public-source
  acquisition is separate from offline preparation, tests and scoring.
- SV-01 is in_review, with technical preparation complete and semantic acceptance
  pending. Next: review PR #2, then SV-02/minimal SV-03B task/input/cost attribution.
  The paid-pilot budget and engineering label owner remain unresolved.

### 2026-10-27 Merge evaluation packets and scoring

- User approved merging PR #2 if the checks were clear. Final review found no
  blocking issue or pending review comments, and all four push/PR CI checks passed
  at 1cd0040 across Python 3.12 and 3.13.
- Merged PR #2 on GitHub at 927f5fb and fast-forwarded local main. Original baseline
  commit 6c819bf and pilot preparation commit 3e5d6da remain in history. Private
  packets, labels and AGENTS.md stay local-only.
- Marked SV-01 and technical preparation done. SV-03 remains in_progress because
  its runtime metadata/readers are still planned. Source labels/context have not
  received engineering approval; no model-quality or cost-saving claim is made.
- Only progress documentation changed in this merge session. Fifteen progress
  links/anchors and whitespace checks passed; all 11 ticket entries remain present.
  Confirmed both frozen commits remain in history and AGENTS.md stays local-only.
  No paid calls or repeat local code tests. Next implementation: SV-02/minimal SV-03B task identity,
  exact input binding, per-attempt spending and compatible resume/export behavior.

### 2026-10-27 SV-02/minimal SV-03B task accounting and compatibility

- User approved the implementation following the best-practices assessment. Added
  task/input fingerprints and explicit evidence revisions, atomic completion records,
  bound split checkpoints, invocation/call identities and a local tasks cost report.
- Preserved OpenRouter reasoning metadata across tool follow-ups with per-invocation
  isolation. Ambiguous histories fail before another paid request; ordinary requests
  retain their settings. Recorded this as the openrouter-v1 compatibility condition.
- New runs use engine openai-agents-v2 and version 2.0 run manifests/results; domain
  schemas stay 1.0 and prompt version stays 5. Old runs still export/read spending,
  with task fields unavailable. Changed output ceilings now require a new run.
- Validation: 202 offline tests, Ruff, mypy, package build, distribution exclusions
  and local links passed. No paid calls or engineering-quality claims.
- Published implementation 373ed26, verified the remote SHA and opened
  [PR #3](https://github.com/noobjam/Project-x/pull/3). All four push/PR checks passed
  on Python 3.12 and 3.13. Main remains at 46e0b06; AGENTS.md remains ignored.
- SV-02 and minimal SV-03B are in_review. Merge remains a separate review decision.
  Next implementation after merge:
  SV-04 retrieval. Paid pilot allocation and label review remain unresolved.

<!-- At each milestone/handoff, update the current sections and append an entry:
Date and milestone; ticket/substep status; changes and safe evidence links;
checks actually run and outcomes; decisions/authorization; blockers and scope;
ordered next action. Include commit/PR references only when they exist.
-->
