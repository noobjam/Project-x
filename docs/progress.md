# Project progress

Last updated: 2026-10-28.

This is the live status and session handoff. Ticket scope and acceptance criteria
are in [the roadmap](agent-roadmap.md); design rationale is in
[the council review](agent-council-review.md). Local sessions also use an ignored
AGENTS.md instruction file; it is intentionally absent from the published tree.

## Current state

- **Active milestone:** SV-05 structured source accounting, in_progress on
  feat/source-obligation-accounting, based on published 784d03c. The user approved
  implementation and the bounded comparison on 2026-10-28. No prerequisite merge
  is needed or authorized. The opt-in implementation is locally complete and
  validated; a $0.28 candidate allocation is reserved within the existing task
  ceiling for the frozen comparison. No new inference has started yet. The initial model screen and one focused prompt
  experiment are complete. The prompt experiment was rejected and reverted;
  engineering-quality acceptance and a successful correction remain pending.
  The current outputs are not suitable for engineer handoff. The source-free
  protocol/results are published in draft
  [PR #6](https://github.com/noobjam/Project-x/pull/6), stacked on PR #5.
- **Measured result:** the unchanged KB-connected workflow on GPT-5 mini / Azure
  Sweden fully preserved 9/13 provisional obligations versus 2/13 for the saved
  Gemini condition. Fully adequate scenarios were 2/13 versus 0/13, with useful
  partial coverage recorded separately. Unsupported expectations and false review
  findings remained. This is a strict, provisional development assessment, not
  engineering approval or proof of KB benefit. See the
  [comparison report](../evals/quality-results-2026-10-28.md).
- **Rejected trial:** prompt version 8 added coverage, observation and review
  instructions. It introduced a false source contradiction and unsupported
  hardware enforcement, then failed on an invalid global-review artifact after
  19 calls ($0.101128324). No retry. The application is restored exactly to prompt
  version 7; model defaults, schemas, orchestration and .env are unchanged.
  Separate-case paid validation was not justified after this regression.
- **Task spending:** $0.2526491055 provider-reported across retained attempts,
  plus $0.308158400 still uncertain from the earlier HTTP 400. Combined commitment
  is $0.5608075055; $0.4391924945 remains within the original $1 ceiling. No calls
  are running. Do not count the reservation as confirmed or silently release it.
- **Implemented connector:** public Markdown/catalog -> frozen per-run JSON ->
  bounded SDK search/read tools, role/task access records and Excel retrieval
  reporting. Code 7ee24a4 is pushed in draft
  [PR #5](https://github.com/noobjam/Project-x/pull/5), stacked on PR #4; neither is
  merged. Required tool use is established; correct application is not.
- **Validation:** the experimental code at a6c9755 passed 244 offline tests,
  Ruff check/format, strict mypy and source/wheel build in this session. The live
  trial failed despite those checks. Restoration returns runtime source to the
  previously validated baseline. Final checks verified 25 local links/anchors,
  no credential patterns in changed documents, ignored/private artifacts and
  exact baseline/candidate inputs. No code tests are claimed for documentation.
- **Current SV-05 checks:** 265-test full offline suite passed, followed by the
  expanded 11-test accounting integration file (including two added CLI/revision
  cases). Ruff, strict mypy (44 files), and source/wheel build passed. Original
  specialist instructions are byte-identical; only the opt-in analyst uses the
  new contract/prompt. This does not establish extraction-quality improvement.
- **Knowledge curation:** revision 2 remains in_review in draft
  [PR #4](https://github.com/noobjam/Project-x/pull/4). All 48 entries remain
  proposed, spanning OpenHW, Accellera, PULP and OpenTitan. No approvals inferred.
- **Acceptance boundary:** the actual Management CPU DOCX remains the full
  acceptance workload. These are small, previously inspected development cases.
  Human answers stay outside retrieval; private source, labels and generated
  output remain ignored under artifacts/. AGENTS.md remains local-only.

## Repository snapshot

Checked on 2026-10-28:

- Local branch: eval/agent-quality-baseline, based on published 90a2ce5 from
  feat/agent-knowledge-tools. Protocol 54493b8, experiment a6c9755 and restoration/
  results 10026da are pushed in draft PR #6. Remote 10026da was verified directly;
  this publication handoff accompanies that branch. The final diff contains only
  shared evaluation/roadmap/progress documents. Runtime matches the PR #5 baseline.
  Main was verified remotely at 52d3241. No merge or private-artifact publication.
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
| Actual KB diagnostic and quality screen | in_progress | KB connection works. One model screen improved extraction but not handoff quality; prompt-only correction regressed and was reverted. Full quality correction, engineering acceptance and KB benefit remain unestablished. |
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
| [SV-05](agent-roadmap.md#sv-05-experiment-with-extraction-coverage-and-interaction-links) | in_progress | Instructions-only coverage trial rejected. Next: reviewable source-obligation accounting for omissions; no expanded schema or index is implemented. |
| [SV-06](agent-roadmap.md#sv-06-evaluate-check-adequacy-before-expanding-planner-schemas) | in_progress | Existing fields scored; prompt trial improved some checks but introduced unsupported assumptions and was rejected. No pattern library or schema expansion. |
| [SV-07](agent-roadmap.md#sv-07-add-typed-review-findings-on-existing-plans) | planned | Typed source/requirement/item findings and local-to-global review; no graph/pattern prerequisite. |
| [SV-08](agent-roadmap.md#sv-08-trial-one-bounded-plan-only-repair) | deferred | Optional existing-item replacement against frozen analysis/partition after usable findings. |
| [SV-09](agent-roadmap.md#sv-09-produce-a-useful-review-view) | planned | Extend CLI/Excel with findings, evidence, limitations and task costs. |
| [SV-10](agent-roadmap.md#sv-10-run-comparisons-throughout-delivery) | in_progress | Frozen 13-label model screen complete; prompt trial rejected and retained as failed. No successful correction, KB-benefit result, engineering acceptance or full-DOCX validation. |
| [SV-11](agent-roadmap.md#sv-11-check-model-feasibility-early-and-route-later) | deferred | A bounded current-endpoint feasibility check belongs to SV-10A; per-role routing is later. |

## Decisions and execution boundaries

- On 2026-10-28 the user approved SV-05: source-linked requirements with explicit
  conditions/values/exceptions and visible skipped/unresolved passages, followed
  by the frozen 13-label comparison on the same model/KB and a separate case only
  if the candidate improves without new unsupported behavior. Implement an opt-in
  bounded-packet trial with a versioned accounting artifact and unchanged V1 plan/
  analysis exports. Exact quotations establish location, not semantic completeness.
  No extra agent role, full-document rollout or SV-07 implementation in this slice.
  Preserve the remaining $0.4391924945 aggregate allocation; no merge.

- The first alternative-model screen retained the same effective source, KB,
  runtime, prompts and generation limits. GPT-5 mini / Azure Sweden completed in
  16 calls at $0.081798244 with no unsettled charge. Provisional full-obligation
  extraction was 9/13 versus 2/13 for the saved Gemini condition, but unsupported
  expectations and review false alarms remained. These are strict complete-label
  judgments; useful partial coverage is recorded separately. No model promotion.
  Admit a bundled instructions-only SV-05/06/review trial, prompt version 8, on
  that model before considering additional schemas. Source was already present,
  so the bounded SV-05 trial may precede SV-04; the roadmap records this exception.

- On 2026-10-28 the user approved the revised evaluation-first approach: freeze
  explicit quality criteria, compare the existing connected workflow with a
  capable alternative model early, and make targeted workflow changes only when
  supported by the evidence. Validate changes on separate development cases.
  Retain the original $1 aggregate ceiling, current EU/ZDR routing constraints,
  private evaluation artifacts and reviewed-PR workflow. This does not authorize
  a merge, a full-document run, the proposed $5 pilot or a claim of engineering
  acceptance. New annotations and our judgments remain agent_proposed.

- On 2026-10-28 the user explicitly rejected testing without connecting the KB.
  Implement bounded search/read tools over a frozen per-run knowledge snapshot,
  record retrieval by role/task, validate offline, then generate actual connected
  output for engineering review within the remaining original $1 task ceiling.
  Proposed entries require an explicit trial opt-in; no engineering approvals
  are inferred. Retrieval is not proof of correct application or better quality.
  Source-only retrieval fixes remain SV-04; no broad schema/agent redesign or merge.

- On 2026-10-28 the user requested actual live output for the engineer. This
  supersedes the earlier documentation-only scope for a bounded local diagnostic.
  The task ceiling was $1; after the first call failed at $0.002845425, two fresh
  workflows each received a $0.49 ceiling. Both used the configured Gemini
  3.1 Flash Lite/Google EU endpoint, identical source and limits, with no repair
  loop. The candidate added only provisional planner guidance. The successful
  executions cost $0.009802925 and $0.009209200; no allocation is silently renewed.
  This is not acceptance of the separate proposed $5 pilot or publication of
  private plans. The needed transport fix is isolated for review; no merge.

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

0. **Active SV-05 comparison:** commit the candidate and freeze its runtime,
   source/KB/configuration/annotation hashes. Run the opt-in workflow once on the
   existing 13-label packet using GPT-5 mini / Azure Sweden, max $0.28, with
   unchanged planner/reviewer prompts and no automatic workflow retry. Inspect
   actual obligations, proposed dispositions, unaccounted spans and downstream
   output against the fixed labels. The original $1 aggregate ceiling and
   outstanding $0.308158400 reservation remain in force. If the candidate improves
   without new unsupported behavior, allocate a separate development-case check
   from the actual remaining balance. Keep source/reference/artifacts private;
   publish a focused review PR, no merge. See the
   [trial protocol](../evals/source-accounting-comparison.md).

0. **SV-05/SV-07 next implementation candidate:** use the frozen failure cases
   to define a small, versioned source-obligation inventory and source-supported
   findings. First concrete action: specify how each explicit obligation is
   retained, marked unresolved or excluded with evidence, and how a finding binds
   both supporting source and the affected claim. Preserve existing output/export
   compatibility and avoid one model call per source block. Mere existence of a
   citation does not establish support; measure semantic errors separately.
   Keep SV-06 observations/pass-fail judgments using existing scenario fields.
   The instruction-only experiment failed; do not layer on more wording or change
   model defaults without evidence. Continue focused, reversible implementation
   within the recorded authorization; no merge. Before another paid comparison,
   freeze the candidate, pass offline checks and record an allocation within the
   remaining $0.4391924945, including the outstanding reservation. A separate
   development case follows only after the candidate clears known regressions.
   Read local experiment.json, assessments and decision.json under
   artifacts/evaluations/model-quality-2026-10-28/ and
   artifacts/evaluations/prompt-quality-2026-10-28/; never pass reference/ to agents.

1. **Knowledge curation:** revision 2 is published in draft PR #4. Use the
   [focused review guide](knowledge/REVISION_NOTES.md)
   for K13–K15, C10, TB06/K03 and E10–E18. Record entry-specific engineering
   decisions with the reviewed commit; resolve or retain the E14 reset conflict.
   The original v1 pack remains a historical snapshot. New source fingerprints
   and validation evidence are under artifacts/evaluations/engineer-review-2026-10-28-v2/.
   Before approved examples guide the agent, define a separate evaluation split
   for an SV-10 comparison. Preserve frozen inventories and reference answers.
   C10's reliable gap-to-row links belong to SV-07/SV-09; this review does not
   implement them or replace SV-04.

2. **Next planned implementation: SV-04.** On the next implementation instruction, create
   a focused branch from current main. First add offline counterexamples for matches
   beyond character 1,000, Unicode coordinates and more than 12 search hits; fix
   match-centered excerpts and stable pagination against the exact task snapshot.
3. **Complete bounded source context.** Add bounded section/neighbor access and
   consistent table-header context in prompts/tools, with explicit warnings when
   support is unavailable. Preserve reference validation, tool permissions and both
   frozen evaluation inventories. No broader roles or general repair are in scope.
4. **Before further paid SV-10 evaluation, resolve its allocation and authorization.** The
   proposed $5 tranche is still unapproved. Check the selected endpoint's tools,
   structured output and reasoning round trips where applicable before comparisons.
   Record reasoning replay as a separate behavior condition. Identify an engineering
   reviewer before semantic-acceptance claims; offline work can continue independently.

## Validation and result references

- Live diagnostic: original packet verification passed (41 blocks). Both outputs
  pass application schemas, source/requirement/item reference checks and workbook
  row/ID checks; exported cells contain text rather than formulas. Both used
  identical source bytes. The local summaries and ledgers reconcile seven total
  attempts including the failed call, with $0.021857550 reported and zero reserved.
  Frozen source/reference inventories were not changed. Review questions are
  provisional observations, not human quality labels. No complete-spec claim.
- Transport fix: gzip/deflate regression tests reproduced DecodingError before
  changing headers. Final 206-test suite, Ruff check/format, mypy (40 source files)
  and sdist/wheel build passed. Compressed SDK integration covers all three roles,
  tool follow-ups, replay without extra calls and unchanged charge accounting.

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

### 2026-10-28: Actual KB integration started

- User clarified that the desired experiment must exercise runtime KB retrieval.
  Started feat/agent-knowledge-tools from the local tested transport fix; initial
  catalog/snapshot and bounded tool edits are local and unvalidated. Runtime and
  CLI integration remain unfinished. No additional paid calls or publication.
- Next: wire frozen knowledge into every specialist task, test the connection,
  run within the remaining original budget, and supply traceable actual output.

### 2026-10-28: KB connector published; live consultation failure caught

- Published 4c136b2 on feat/agent-knowledge-tools and verified the remote SHA;
  opened draft PR #5 with PR #4 as its base. 239 offline tests, Ruff, mypy and
  source/wheel build passed. Private sources, plans and AGENTS.md stay excluded.
- The new baseline completed; the candidate returned without calling knowledge
  tools. The final guard rejected it. Its $0.002640825 charge is retained alongside
  the $0.008634725 baseline charge; cumulative task spending is $0.033133100,
  with zero unsettled reservations. Artifacts: live-kb-review-2026-10-28-v1.
- Added required API tool choice for search then read, returning to automatic
  choice after consultation. Installed-SDK regression checks verify each request;
  the configured endpoint advertises tool_choice support. Revalidate and pin a
  fresh matched pair before claiming successful KB execution.

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

### 2026-10-28: Live reset-packet review trial and transport fix

- User requested actual generated outputs. First run
  70491ac9-5373-4cd7-b0ae-e216755ba448 failed after one paid response; retained its
  $0.002845425 charge and artifacts. Reproduced double decompression offline and
  committed the narrow header fix with regression tests as be849b6. No model or
  provider switch, permanent prompt change or schema change was needed.
- Fresh baseline cd1e9727-8e07-4213-925b-9fccab50de9f and candidate
  6b05182f-bf2d-4de0-8219-d0a199e46f7e completed with needs_review. Both contain
  seven extracted requirements, but different obligations; the candidate has
  four plan items versus six baseline items. Counts are not quality scores.
- Provisional guidance was injected only into candidate planner instructions by
  an ignored local runner. Exact instructions, guidance, source hashes, code
  commit, task bindings and charge ledgers are preserved. Independent extraction
  and model variability limit this comparison. Previously inspected development
  evidence is not held-out gold, and no engineer answers were supplied.
- Prepared two Excel plans, exact JSON artifacts, source text, a review guide and
  a separate feedback form under the ignored live-review-2026-10-28-v2 directory.
  Final charge $0.021857550 including failure; no unsettled charges. The engineer
  should assess the outputs before further knowledge expansion or larger runs.
- Offline fix validation passed 206 tests plus lint, formatting, types and build;
  live outputs passed structural/workbook checks. Branch publication remains the
  delivery step; merging and engineering acceptance remain pending.

### 2026-10-28: Actual KB execution and private engineering package

- Final implementation 7ee24a4 is pushed in draft PR #5 and directly verified on
  origin. PR #5 depends on the curation branch in PR #4; neither is merged.
  All 244 offline tests, lint/format, mypy and build passed; all four code-head
  GitHub checks passed on Python 3.12/3.13. Final handoff edits are documentation only.
- Live failures were retained: prompt-only consultation was skipped; forced tool
  calls with a final-output schema were rejected by the provider; an invalid read
  violated tool bounds; one analysis cited an unknown source ID. Required tool
  choice, separate tool/final-output schemas, declared read bounds and safe SDK
  error handling address integration failures. They do not guarantee good plans.
- Candidate 1101a7f7-8012-439f-8387-a00c134f924f completed with needs_review and
  actual search/read access by analyst, planner and reviewer. It used eight public
  proposed entries, with full selected-entry text returned, and cost $0.0192188975.
  Source-only comparison ffc6a8a4-d2db-4a72-94e9-926e05103455 failed missing-requirement
  validation twice, including one resume, and cost $0.00923494. No accepted baseline
  plan or comparative quality improvement is claimed.
- Prepared an ignored 65-file engineer package with the candidate workbook, exact
  source and frozen KB, retrieval/task/charge records, failed-comparison evidence,
  provisional observations and blank feedback form. Workbook rows/IDs, formula
  safety, matching source/code/settings, ZIP integrity and all file hashes passed.
  Artifact root: artifacts/evaluations/live-kb-review-2026-10-28-v4/.
- Aggregate provider-reported cost is $0.0697225375; the earlier HTTP 400 retains
  a separate $0.308158400 uncertain reservation. All remain within the original
  $1 task ceiling. No further paid runs, engineering approval or merge.
- Next: engineer review of the actual candidate and selected KB entries, then
  a focused fix to adjudicated omissions/application errors and another bounded
  comparison under an explicitly recorded allocation. SV-10 remains in_progress;
  the broader SV-04 source-retrieval ticket remains planned.

### 2026-10-28: Engineer handoff held after output assessment

- User rejected the current output as unsuitable for engineer review and asked
  whether architecture explains the failures. Inspected extraction, knowledge
  consultation, plan validation and reviewer contracts against the actual run.
- Identified structural gaps in completeness and evidence checks; the model's
  contribution remains unmeasured. Preserve the three-role runtime while defining
  focused quality changes rather than assuming more knowledge or more agents fixes
  the observed failures. No code changes, new tests, inference or publication in
  this assessment session; this checkpoint is local and uncommitted.
- The existing package remains historical diagnostic material. Its handoff
  invitation is withdrawn pending internal correction; no engineering approval.

### 2026-10-28: Model screen complete; prompt-only correction rejected

- Committed the source-free protocol at 54493b8. Froze 13 source-bound provisional
  obligations before the new model output; verified source, KB, runtime versions
  and effective settings against the saved Gemini baseline. Reused existing
  scoring contracts; no answers/annotations entered the runtime context.
- GPT-5 mini / azure/swedencentral completed in 16 calls at $0.081798244, zero
  reserved. Provisional full-obligation extraction 9/13 versus 2/13; adequacy
  2/13 versus 0/13. Both retained useful partial checks. The larger output also
  contained unsupported expectations; its reviewer produced false/mixed findings.
  This does not select a best model or establish KB benefit.
- Trial a6c9755 changed only versioned instructions across the three roles. All
  244 offline tests, Ruff check/format, mypy and source/wheel build passed.
  The live run produced a new false contradiction and unsupported hardware
  enforcement, then failed in global review with an invalid structured artifact.
  Retained 19 calls, $0.101128324, zero reserved; no retry or separate-case run.
- Rejected the trial and restored prompt version 7 exactly. Frozen experiment
  commit/artifacts preserve the failed condition. No production model or schema
  change is accepted. The next candidate needs inspectable source accounting and
  supported findings, with semantic grading separate from reference validation.
- Current task total: $0.2526491055 reported plus $0.308158400 uncertain;
  $0.4391924945 remains under the original $1 ceiling. No engineering acceptance.
  Final documentation/privacy/provenance checks passed. Published restoration/
  results at 10026da in draft PR #6 and verified the remote SHA directly. Push CI
  passed for 10026da; its PR CI was still running when this handoff was written.
  This publication-status update is the only follow-up change.

<!-- At each milestone/handoff, update the current sections and append an entry:
Date and milestone; ticket/substep status; changes and safe evidence links;
checks actually run and outcomes; decisions/authorization; blockers and scope;
ordered next action. Include commit/PR references only when they exist.
-->
