# Project progress

Last updated: 2026-10-28.

This is the live status and session handoff. Ticket scope and acceptance criteria
are in [the roadmap](agent-roadmap.md); design rationale is in
[the council review](agent-council-review.md). Local sessions also use an ignored
AGENTS.md instruction file; it is intentionally absent from the published tree.

## Current state

- **Live review trial:** in_progress, limited SV-10A/B diagnostic on the frozen
  Management CPU reset packet on fix/openrouter-compressed-response. The user
  requested actual generated output after the knowledge review handoff. Allocate
  at most $1 total: the first attempt failed after a confirmed $0.002845425 charge;
  reserve $0.49 each for the current planner and the workflow with provisional K13/K15,
  C10 and TB06 planning guidance. Same source, model/provider and limits; no
  reference answers or worked examples enter context. This is a local exploratory
  trial, not engineering acceptance or approval of the separate $5 pilot proposal.
  Keep outputs private and report failures and unsettled charges within the cap.
- **Transport fix:** the first live response exposed double decoding of buffered
  compressed responses. Offline gzip/deflate regressions failed before the fix.
  Rebuilding encoding/length/framing headers resolves them; compressed SDK tool
  loops and accounting pass. Full validation: 206 tests, Ruff check/format, mypy
  and source/wheel build passed. Prompts and domain schemas are unchanged.
- **Active milestone:** knowledge curation revision 2, in_review on
  docs/knowledge-curation-review for draft PR #4. Published at 82d401c and verified
  against the remote branch. The [focused review guide](knowledge/REVISION_NOTES.md)
  maps all four comments from 5a1aah to the changes and remaining decisions.
  No entries are engineering-approved or connected to runtime retrieval.
- **Phase:** the baseline foundation is merged through
  [PR #3](https://github.com/noobjam/Project-x/pull/3) at 82db1c2. SV-02 and the
  limited SV-03 scope are done: exact task/input bindings, per-call spending,
  compatible readers and OpenRouter reasoning replay. Engineering acceptance is pending.
- **Current working plan:** a smaller first release focused on source retrieval,
  structured findings, agent task/cost reporting and reviewable output, evaluated
  against the real Management CPU DOCX.
- **Implemented baseline:** OpenAI Agents SDK analyst/planner/reviewer agents,
  bounded evidence tools, OpenRouter transport, Python orchestration, immutable
  artifacts and Excel export. LangGraph/LangChain were removed.
- **Next implementation milestone:** SV-04 retrieval and bounded source context. Implementation
  has not started. PR #3 passed all four push/PR CI checks at final head 95ae453
  on Python 3.12/3.13; its implementation validation included 202 offline tests,
  Ruff, mypy and source/wheel build. The merge session verified those results.
- **No new paid evaluation:** the migrated runtime has not yet had a paid live
  engineering evaluation. Quality and savings remain unmeasured.
- **Original knowledge handoff:** the ignored v1 HTML/ZIP pack is an unchanged
  historical snapshot with 40 draft entries: 12 planning questions,
  seven testbench groups (21 subchecks), 12 source-backed patterns and nine worked
  examples. Sources span OpenHW, Accellera, PULP and OpenTitan, plus private
  examples; a source inventory records versions, hashes and original files.
  Comparable-system source usage is documented separately. No entries have been
  approved or integrated into the runtime; canonical evaluation files are intact.
- **Curation review scope:** revision 2 has 48 proposed public entries: 15
  patterns, 12 planning questions, seven testbench groups (21 subchecks) and 14
  examples across OpenTitan, PULP AXI, CV32E40P and CORE-V MCU. K13–K15 adapt
  the engineer's proposals; C10 and TB06/K03 address completion and evidence.
  E10–E18 add transferable cases, pinned sources and an explicit reset-value
  conflict in E14. The four private examples and original CPU material remain
  excluded. [PR #4](https://github.com/noobjam/Project-x/pull/4) remains draft and
  unmerged; revision 2 is published and awaits focused engineering confirmation.
- **Local instructions:** AGENTS.md stays on the Mac and is excluded from Git.
  The roadmap, council review and this progress tracker remain shared documents.

## Repository snapshot

Checked on 2026-10-28:

- Local branch: docs/knowledge-curation-review; revision 2 content committed and
  published at 82d401c, directly verified remotely before this handoff update.
  main remains at 52d3241 (verified remotely). The revision changes only nine
  review/progress Markdown files. AGENTS.md remains local-only and ignored.
- Migration commit: 5d15c10; preserved pre-migration prototype: 10f5bad.
- Push destination: https://github.com/noobjam/Project-x.git. GitHub reports PR #3
  merged at 82db1c2; implementation 373ed26 and reviewed head 95ae453 remain in
  history. Frozen baseline 6c819bf and pilot 3e5d6da are unchanged.
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
| Baseline foundation | done | SV-02/minimal SV-03B merged in PR #3 at 82db1c2. Exact snapshots, task/call spending, strict resume, legacy readers and reasoning replay passed offline checks and final-head CI. Paid evaluation remains pending. |
| Knowledge curation revision 2 | in_review | Published at 82d401c in draft PR #4. Four engineering comments incorporated; 48 entries including 14 public examples. Documentation checks passed; entry-specific engineering confirmation pending. This does not complete SV-04 or SV-06. |
| Retrieval and review release | planned | SV-04, SV-07 and SV-09, with SV-10 comparisons during delivery. |
| Full real-workload acceptance | planned | SV-10D after useful slice evidence, declared funding and engineering review. |

## Ticket status

All scopes below link to their acceptance criteria. No implementation ticket is
complete merely because its plan exists.

| Ticket | Status | Current position and next step |
| --- | --- | --- |
| [SV-01](agent-roadmap.md#sv-01-freeze-the-real-workload-pilot-and-evaluation-contract) | done | A: merged in PR #1. B/C: merged in PR #2 with five verified packets, 37 provisional/disputed labels, scoring controls and a frozen inventory. Technical preparation is complete; engineering-quality acceptance is pending. |
| [SV-02](agent-roadmap.md#sv-02-bind-agent-work-to-input-snapshots-and-spending) | done | Merged in PR #3 at 82db1c2: exact task/input bindings, atomic completions, per-call attribution and local task spending. |
| [SV-03](agent-roadmap.md#sv-03-establish-minimal-evidence-and-compatibility-contracts) | done | A merged in PR #1; limited B merged in PR #3. Task/run versions, exact inputs, stale-resume rejection and legacy readers are complete. Typed findings stay in SV-07. |
| [SV-04](agent-roadmap.md#sv-04-correct-retrieval-and-bounded-source-context) | planned | Fix matching excerpts, pagination and bounded table/neighbor context after minimal contracts. |
| [SV-05](agent-roadmap.md#sv-05-experiment-with-extraction-coverage-and-interaction-links) | deferred | Start only if measured extraction/cross-section failures justify it. |
| [SV-06](agent-roadmap.md#sv-06-evaluate-check-adequacy-before-expanding-planner-schemas) | deferred | Evaluate existing scenario fields first; patterns/schema expansion require evidence. |
| [SV-07](agent-roadmap.md#sv-07-add-typed-review-findings-on-existing-plans) | planned | Typed source/requirement/item findings and local-to-global review; no graph/pattern prerequisite. |
| [SV-08](agent-roadmap.md#sv-08-trial-one-bounded-plan-only-repair) | deferred | Optional existing-item replacement against frozen analysis/partition after usable findings. |
| [SV-09](agent-roadmap.md#sv-09-produce-a-useful-review-view) | planned | Extend CLI/Excel with findings, evidence, limitations and task costs. |
| [SV-10](agent-roadmap.md#sv-10-run-comparisons-throughout-delivery) | planned | A baseline, B incremental comparisons, C optional repair experiment, D full-DOCX acceptance. Preparation may proceed offline. |
| [SV-11](agent-roadmap.md#sv-11-check-model-feasibility-early-and-route-later) | deferred | A bounded current-endpoint feasibility check belongs to SV-10A; per-role routing is later. |

## Decisions and execution boundaries

- On 2026-10-28 the user said to keep moving after the proposed revision of
  PR #4. Revise and publish the knowledge review documents: K13–K15, broader
  public examples, C10, TB06/K03 and the progress handoff. This is documentation
  curation, not authorization to merge, integrate knowledge, execute EDA tools or
  run paid inference. No implementation ticket scope has changed.

- On 2026-10-27 the user approved merging PR #3 if checks were clear and requested
  the next move. Final review found no blocking issue or pending review comment;
  all four CI checks passed on exact head 95ae453. Merged at 82db1c2 and synced
  local main. This completes the merge/handoff; SV-04 implementation and paid
  evaluation have not been started or authorized by this merge request.

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
- The user's engineering reviewer, GitHub account 5a1aah, supplied four PR #4
  comments on 2026-10-27. These propose additions/corrections, not blanket
  approval. Revision 2 asks for confirmation of the edited entries, applicability
  and unresolved source conflicts. Semantic acceptance still requires reviewed
  labels and measured plan quality.
- The user clarified that this handoff is for knowledge-base content curation,
  with substantive material from multiple credible sources and a comparison of
  sources used by similar agents. Testbench subchecklists are planning knowledge,
  not authorization to build a testbench or a readiness claim. Keep original
  passages separate from proposed adaptations. Existing examples promoted to
  runtime knowledge would no longer be independent evaluation cases; select
  separate held-out material before measuring benefit. Runtime integration and
  paid evaluation have not been started by this handoff.
- On 2026-10-27 the user asked to push the curation material to GitHub for
  engineering review. Publish the public-source Markdown edition on
  docs/knowledge-curation-review and open a draft review PR. The repository is
  public; keep private examples and the full local pack ignored. This authorizes
  publication of the review documents, not a merge or runtime integration.
- Private reference material already inspected is development/acceptance-regression
  evidence, not blind gold. Missing visual evidence remains a visible limitation.
- Revisions are currently disabled in the recorded run configuration. Optional
  repair adds capability and cost; do not claim it saves existing repair spending.
- Model selection, Booley/JEV, execution tools, automatic diagram interpretation
  and broader agent teams remain deferred according to the roadmap.

## Next moves

0. **Knowledge curation:** revision 2 is published in draft PR #4. Use the
   [focused review guide](knowledge/REVISION_NOTES.md)
   for K13–K15, C10, TB06/K03 and E10–E18. Record entry-specific engineering
   decisions with the reviewed commit; resolve or retain the E14 reset conflict.
   The original v1 pack remains a historical snapshot. New source fingerprints
   and validation evidence are under artifacts/evaluations/engineer-review-2026-10-28-v2/.
   Before approved examples guide the agent, define a separate evaluation split
   for an SV-10 comparison. Preserve frozen inventories and reference answers.
   C10's reliable gap-to-row links belong to SV-07/SV-09; this review does not
   implement them or replace SV-04.

1. **Next implementation: SV-04.** On the next implementation instruction, create
   a focused branch from current main. First add offline counterexamples for matches
   beyond character 1,000, Unicode coordinates and more than 12 search hits; fix
   match-centered excerpts and stable pagination against the exact task snapshot.
2. **Complete bounded source context.** Add bounded section/neighbor access and
   consistent table-header context in prompts/tools, with explicit warnings when
   support is unavailable. Preserve reference validation, tool permissions and both
   frozen evaluation inventories. No broader roles or general repair are in scope.
3. **Before paid SV-10A evaluation, resolve its allocation and authorization.** The
   proposed $5 tranche is still unapproved. Check the selected endpoint's tools,
   structured output and reasoning round trips where applicable before comparisons.
   Record reasoning replay as a separate behavior condition. Identify an engineering
   reviewer before semantic-acceptance claims; offline work can continue independently.

## Validation and result references

- Knowledge revision 2: checked 48 unique entry IDs, 14 public examples, 21
  testbench subchecks, local links/anchors, six new pinned source-file hashes
  and cited line-range bounds. The nine-file Markdown allowlist, credential
  patterns, exclusion of private example entries and AGENTS.md ignore/tracking
  checks passed. Source facts were compared with the cited documents, including
  UVM chapter 5 and the mailbox reset conflict. Whitespace checks passed.
  No local code tests, HDL/formal runs or paid model calls were performed.
  Engineering approval and measured knowledge benefit remain pending.

- PR #3 merge check: all four push/PR CI checks passed on final head 95ae453,
  covering Python 3.12 and 3.13. No pending review comments or blocking findings.
  Merged as 82db1c2 and fast-forwarded local main. Only this progress document
  changed during the merge session; links/anchors and whitespace checks passed.
  Code tests were not repeated and no paid inference was performed.

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

### 2026-10-27 Merge task accounting and compatibility

- User approved merging PR #3 after final checks. No blocking review issue or
  pending comment remained; all four CI checks passed on exact head 95ae453.
- Merged on GitHub at 82db1c2 and fast-forwarded local main. Marked SV-02, limited
  SV-03 and the baseline foundation done. Preserved both frozen evaluation commits
  and the local-only AGENTS.md. Quality and savings remain unmeasured.
- Updated the handoff and next actions. Documentation links/anchors, whitespace,
  ticket status coverage and local-instruction exclusion checks passed. No runtime
  edits, repeat software tests or paid calls were needed for this merge session.
- Next implementation: SV-04 matching excerpts, stable pagination and bounded
  table/neighbor context on a new branch. Paid SV-10A funding and engineering label
  review remain separate pending decisions.

### 2026-10-27: Knowledge curation pack prepared locally

- User requested material their verification engineer can curate, then clarified
  the objective as a rich knowledge-base starting set rather than broader
  acceptance or testbench implementation. Broadened source selection beyond
  OpenTitan to OpenHW CORE-V-VERIF, Accellera UVM and PULP, with an authoritative
  RISC-V cross-check and evidence on five comparable systems' data usage.
- Created an ignored HTML review page and ZIP with original documents, source
  excerpts, provenance, 40 proposed knowledge entries, 21 testbench subchecks,
  reviewer fields and portable save/load. The five existing cases and 37
  provisional/disputed interpretations remain supporting development material.
- Pack path: artifacts/evaluations/engineer-review-2026-10-27-v1/.
  No private excerpts or reference answers were added to tracked documentation.
  No source/runtime changes, paid calls, approvals, commits or pushes were made.
- Validation: frozen pilot verified (22 pinned files); local Chrome exercised
  navigation, filters, correction validation, save/download/import, autosave and
  version mismatch rejection. No page network requests or JavaScript exceptions.
  Desktop/mobile layout inspected and a layout issue corrected. All 59 bundled
  file fingerprints, local source links and ZIP integrity checked. Engineering
  curation and measured knowledge benefit remain pending; next action is the
  engineer's review.

### 2026-10-27: Public knowledge review documents published

- User requested GitHub publication for engineering review. Prepared the public
  edition on docs/knowledge-curation-review: 36 candidate entries, 21 testbench
  subchecks, public evidence, source provenance, comparable-system data usage,
  review instructions and license attribution. Added the entry point to README.
- The four private examples, original CPU documents, source annotations, full
  local ZIP/HTML pack and local-only instructions remain excluded from Git.
- Committed as b65a617, pushed to noobjam/Project-x on
  docs/knowledge-curation-review and verified the remote SHA directly. Opened
  [draft PR #4](https://github.com/noobjam/Project-x/pull/4) for engineering review.
  Not merged; reviewer decisions and knowledge integration remain pending.
- Validation: 36 unique entry IDs, five allowlisted public examples, 21 subchecks,
  46 local documentation links, an explicit publication file allowlist, private
  source/identifier screening and credential-pattern checks passed. No runtime
  changes, paid calls or new engineering approvals. Local code tests were not
  rerun for this documentation-only publication; GitHub CI runs separately.

### 2026-10-28: Knowledge review revision 2 published

- Incorporated all four comments from 5a1aah into proposed revisions: K13–K15
  for clock/reset, data/control and registers; C10 for automatic draft completion
  with linked source gaps; TB06/K03 for appropriate evidence without mandatory
  covergroups. Added a comment-to-change review guide and focused questions.
- Expanded worked examples from five to 14 across four projects. E10–E18 use
  pinned PULP AXI, CV32E40P and CORE-V MCU documents; source summaries, proposed
  checks, missing inputs and transfer limits are separate. E14 retains a newly
  identified reset-value conflict. All 48 entries remain proposed.
- Local documentation checks passed as recorded above. Only review/progress
  Markdown changes; source downloads and validation evidence stay ignored.
  AGENTS.md and private/frozen material remain unchanged. No runtime changes,
  code-test rerun, paid evaluation, merge or engineering approval is claimed.
- Committed and pushed as 82d401c to the existing draft PR #4; its full remote
  SHA matched the local commit. The PR remains draft and unmerged. The next
  action is entry-specific engineer confirmation using the focused review guide.
  SV-04 is still planned; runtime knowledge integration requires a separately
  defined evaluation split.

<!-- At each milestone/handoff, update the current sections and append an entry:
Date and milestone; ticket/substep status; changes and safe evidence links;
checks actually run and outcomes; decisions/authorization; blockers and scope;
ordered next action. Include commit/PR references only when they exist.
-->
