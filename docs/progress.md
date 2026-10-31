# Project progress

Last updated: 2026-10-31.

This is the live status and session handoff. Ticket scope and acceptance criteria
are in [the roadmap](agent-roadmap.md); design rationale is in
[the council review](agent-council-review.md). Local sessions also use an ignored
AGENTS.md instruction file; it is intentionally absent from the published tree.

## Current state

- **Merged foundation:** PR [#9](https://github.com/noobjam/Project-x/pull/9)
  adds CI/merge safeguards; [#4](https://github.com/noobjam/Project-x/pull/4),
  [#5](https://github.com/noobjam/Project-x/pull/5) and
  [#6](https://github.com/noobjam/Project-x/pull/6) are merged. Remote main is
  9447b33. Required current-base CI and resolved conversations are enforced;
  force push/deletion and administrator bypass are disabled. The single
  maintainer has no mandatory external-approval count.
- **Active milestone:** SV-07 offline correction is technically complete on
  fix/source-inventory-contract, based on published recovery results 2d104ec in
  draft [PR #10](https://github.com/noobjam/Project-x/pull/10). Existing
  inventory fact-list rules are now in the outgoing schema; audit instructions are
  clarified at prompt 14 in draft [PR #11](https://github.com/noobjam/Project-x/pull/11).
  The correction is in_review; code head 719235c is pushed and all three CI checks
  passed. SV-10 recovery assessment is complete; paid quality evaluation remains pending.
- **Measured quality:** calibration detects 5/5 seeded defects, with four fully
  supported primary corrections, three unsupported extras and one duplicate;
  0/3 valid-control false alarms. Real extraction covers 6/13 frozen labels,
  down from 9/13. All thirteen were assessed. No comparison audit or plan ran.
  See [results](../evals/source-first-results-2026-10-30.md).
- **Failure diagnosis:** all 62 inventory passage IDs were returned exactly once,
  but 17 context entries contained facts prohibited by the persisted contract.
  The outgoing schema did not encode that rule. Offline replay reproduces the
  rejection; no rejected response was edited into success. The correction exposes
  the rule in generation schema/instructions, retaining host validation and old readers.
- **Spending:** V2 used six calls / $0.046524588 reported / $0 reserved. This
  comparison totals $0.150656803 reported plus $0.136400000 uncertain from V1.
  Aggregate reported is $0.5703545485; uncertain reservations remain $0.444558400.
  Combined $1.0149129485 leaves $0.2350870515 under the approved $1.25 ceiling.
  No uncertain charge was released. The approved V2 attempt is consumed;
  remaining allowance does not authorize another paid condition.
- **Validation:** the outgoing-schema regression failed before the fix and now
  passes through the actual SDK/gateway request path. All 354 offline tests pass
  (91% coverage), Ruff, strict mypy (49 files) and build pass. All eight historical
  prompt-13 calibration audits remain readable with their receipts. The host still
  rejects invalid context/fact combinations; persisted formats are unchanged.
  Prompt 14 has no paid quality result. No model call followed V2's failure.
- **Knowledge and acceptance:** 48 proposed public KB entries and their connector
  are now on main; merge does not confer engineering approval. Actual KB reads
  were measured, but benefit remains unestablished and some applications were
  unsupported. Management CPU DOCX is the acceptance workload; reference answers
  stay outside retrieval. Private inputs/outputs remain ignored under artifacts/.
  AGENTS.md remains local-only. Model defaults and environment settings are unchanged.

## Repository snapshot

Checked against GitHub on 2026-10-31:

- Push destination: https://github.com/noobjam/Project-x.git.
- Main: 9447b33b076ae8c56b619d6bf323769fb6040d71. Merge commits: PR #9
  4458169, #4 e78e2ea, #5 69ac52d, #6 9447b33. Each merge used its exact reviewed
  head after all three protected checks passed; no administrator bypass.
- Draft [PR #7](https://github.com/noobjam/Project-x/pull/7) targets main at
  eff6d846e0e6cd9b56b0c5ec66a67a226feae084. Draft
  [PR #8](https://github.com/noobjam/Project-x/pull/8) targets #7 at
  d342406cdaa39b385a2df3f962e7d44122bd72fc. Both include the merged safeguards;
  all three checks passed on these exact heads. Their measured quality limits
  remain visible and the experimental stack is unmerged.
- Experimental source-first branch: feat/source-first-audit in draft PR #10, targeting #8.
  Recovery results are published at 2d104ec7fc08c6fd32ee06364cbbe21d59d7107f;
  its remote SHA was verified directly. Implementation 0e345be and integration
  f847788 are included. Correction branch fix/source-inventory-contract in draft
  PR #11 targets #10. Published code head 719235c9a9ded4f6fc1e729968783308b9558bf7
  was verified directly on origin; all three protected CI checks passed. This
  documentation checkpoint follows that code; use Git for the final docs SHA.
  Local main remains 9447b33.
  Historical experiment commits are preserved, not rewritten.
- Migration commit 5d15c10, pre-migration prototype 10f5bad, PR #3 merge 82db1c2,
  frozen baseline 6c819bf and pilot 3e5d6da remain unchanged.
- AGENTS.md was removed from tracking at 82df541 and remains ignored locally.
  No private evaluation artifacts are published.

Recheck Git state on resume; this snapshot is not a permanent assertion.

## Milestone status

| Milestone | Status | Evidence and remaining work |
| --- | --- | --- |
| SDK migration | done | Merged at 7c2f05d and published to GitHub in the push through 2bb4293. Last recorded validation: 112 tests passed, Ruff, mypy and build passed. These checks were reported in the migration session, not rerun for publication. |
| Research council and plan revision | done | Three tracks reviewed dataset relevance, architecture and delivery/cost. Final review found no blocking planning issue; see the council review. This is not semantic validation of agent outputs. |
| Session continuity documentation | done | Local agent instructions and shared progress tracker created. Initial documentation checks passed. AGENTS.md is now local-only; roadmap, council review and progress remain published. |
| Preparation | done | SV-01A/SV-03A merged in PR #1; SV-01B/C merged in PR #2 at 927f5fb. Five local packets, 37 provisional/disputed labels, scoring controls and the frozen inventory are technically complete. Context/label engineering review and paid evaluation remain separate. |
| Baseline foundation | done | SV-02/minimal SV-03B merged in PR #3 at 82db1c2. Exact snapshots, task/call spending, strict resume, legacy readers and reasoning replay passed offline checks and final-head CI. Paid evaluation remains pending. |
| Knowledge curation revision 2 | in_review | Merged through PR #4 at e78e2ea. Four engineering comments incorporated; 48 entries including 14 public examples remain proposed. Entry-specific engineering confirmation is pending; merging does not complete SV-04 or SV-06. |
| Source-first audit correction | in_review | Draft PR #10; 347 offline tests and all three CI checks pass. Calibration detects 5/5 defects but emits three extra unsupported findings. Recovery completed extraction but inventory was rejected. Prompt-14 follow-up passes 354 offline tests; live quality is unmeasured. Semantic acceptance remains unmet. |
| Actual KB diagnostic and quality screen | in_progress | Latest calibration and all thirteen recovery extraction labels assessed. Recovery is 6/13, down from 9/13; no accepted real audit. Full quality correction, engineering acceptance and KB benefit remain unestablished. |
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
| [SV-05](agent-roadmap.md#sv-05-experiment-with-extraction-coverage-and-interaction-links) | in_progress | Latest real extraction covers 6/13; all labels assessed, below the previous 9/13. No quality promotion or full-document expansion; interaction index remains deferred. |
| [SV-06](agent-roadmap.md#sv-06-evaluate-check-adequacy-before-expanding-planner-schemas) | in_progress | Existing fields scored; prompt trial improved some checks but introduced unsupported assumptions and was rejected. No pattern library or schema expansion. |
| [SV-07](agent-roadmap.md#sv-07-add-typed-review-findings-on-existing-plans) | in_progress | Source-first auditor detects 5/5 control defects, with four supported primary corrections, three unsupported extras and one duplicate; 0/3 valid-control false alarms. Real inventory failed validation; comparison quality remains unmeasured. Schema/prompt correction is technically complete offline; live validation is pending. Full plan review remains planned. |
| [SV-08](agent-roadmap.md#sv-08-trial-one-bounded-plan-only-repair) | deferred | Optional existing-item replacement against frozen analysis/partition after usable findings. |
| [SV-09](agent-roadmap.md#sv-09-produce-a-useful-review-view) | planned | Source audit/accounting CLI and Excel views delivered in the bounded slice. Full scenario-to-source review view remains planned. |
| [SV-10](agent-roadmap.md#sv-10-run-comparisons-throughout-delivery) | in_progress | Calibration and recovery assessed in PR #10; all eight controls/thirteen real labels retained. Approved V2 failed inventory validation after 6/13 extraction; both failed attempts preserved. No new full plan or engineering acceptance. |
| [SV-11](agent-roadmap.md#sv-11-check-model-feasibility-early-and-route-later) | deferred | A bounded current-endpoint feasibility check belongs to SV-10A; per-role routing is later. |

## Decisions and execution boundaries

- Prepared, not authorized or executed: fixed-candidate auditor condition at
  code 719235c / prompt 14, maximum $0.20 / 12 calls. Condition SHA-256
  3c41a6acceb1909ff1303aa6a97a837751147e47b1661b301cedcb1ba96a136c.
  It reuses V2 extraction without modifications. The inventory sees only source
  and KB; the comparison then sees the fixed candidate. All thirteen labels and
  every finding remain in scope. Worst-case comparison commitment $0.487056803
  stays below $0.49; aggregate $1.2149129485 stays below $1.25, retaining all
  uncertain reservations. No additional total allowance is requested.
- On 2026-10-31 the user explicitly approved prepared recovery V2 with “lets go
  for it !” after the bounded next-step explanation. The condition is capped at
  $0.24 / 24 calls, with unchanged model, KB, source, prompt and generation limits.
  Reallocate unused comparison allowance while retaining the interrupted attempt
  and its full reservation; the $0.49 comparison and $1.25 aggregate caps remain.
  Authorization is recorded locally against condition hash 19b40390. Execution and
  assessment are complete and the one attempt is consumed. No additional paid
  condition is implied; offline corrections remain authorized.
- The approved 2026-10-30 calibration completed; the real V1 condition was
  interrupted by observed ENOSPC and exit 120 before analysis. Do not restart it
  silently or release the missing response's reservation. Recovery V2 is prepared
  with unchanged runtime/inputs and a $0.24 cap, using unused calibration allowance
  while retaining both the $0.49 comparison and $1.25 aggregate ceilings. Explicit
  approval for this reallocation/retry was subsequently granted on 2026-10-31;
  both original and recovery approvals remain recorded. No request for a larger total budget is needed.
- On 2026-10-30 the user authorized CI/merge enhancements, merging eligible work
  and continuing toward an engineer demo with Synopsys as a reference. PR #9 and
  reviewed foundation PRs #4/#5/#6 are merged. This supersedes earlier no-merge
  boundaries for those PRs. Keep #7/#8 and the new correction as experimental
  drafts while quality is unproven. The authorization covers implementation,
  offline validation and publication; no fresh paid allocation was specified.
  The optional deadline/demo-scope clarification remains unanswered.
- Approved on 2026-10-30 by the user's “go for it” after the explicit budget request: $0.25 / 96 calls for all eight source-first
  controls, then $0.24 / 24 calls for one real analysis-only condition if controls
  complete and their assessment supports a diagnostic run. Raising the aggregate
  ceiling to $1.25 covers $0.7278561455 already committed plus $0.49 new caps
  ($1.2178561455 total). No uncertain reservation is released. Immutable local
  authorization records bind each frozen condition; do not ask for this scope again.
- The 2026-10-29 calibration and real-packet conditions are finished. V2 supplied
  usable outputs for a diagnostic real extraction/audit, not semantic approval.
  The real result fails the quality gate: equal aggregate extraction hides two
  regressions, and the auditor does not detect the incomplete labels. Keep the
  baseline, feature opt-in and audit advisory. Record the next SV-07 correction
  without starting another paid condition, changing models or merging the stack.
  Final results/docs publication belongs to the already authorized PR #8 handoff.
- After the first calibration failed, the authorized calibration continued with
  a separately versioned corrective candidate: passage/requirement
  enums and a clear distinction between extraction defects and optional source
  elaboration. All frozen cases, labels, KB/model and generation limits were kept.
  Its allocation was $0.19 / 45 calls from the unspent calibration allowance;
  the previous 3 calls/$0.00940995 remain charged. The condition required offline
  checks and freezing before inference, stopping on another execution failure,
  and usable calibration output before the $0.18 real-packet allocation. Both
  conditions are now finished as recorded above. No automatic semantic gate.
- The user's latest “alright lets go for it” approves the stated next step:
  SV-10 runner plus measured auditor calibration, followed by bounded real-packet
  evaluation under the existing aggregate allowance. Declare $0.20 for eight
  synthetic candidates and $0.18 for one analysis-only real-packet condition
  (sum $0.38 <= $0.3845682655 remaining). Preserve the uncertain old reservation.
  Use GPT-5 mini / Azure Sweden and the frozen KB. Calibration caps each output
  at 4,000 tokens; the real packet retains 12,000. Freeze all effective limits,
  source/KB hashes and code before inference. No silent retry or larger allocation.
  Implement, validate and publish on eval/source-audit-calibration; no merge.
- On 2026-10-29 the user approved ticket updates and implementation of the
  researched next slice. The roadmap now specifies V3 passage dispositions,
  structured feedback with one disposition-only correction, an advisory source
  audit and analysis-only execution. Existing procedures can be referenced through
  proposed application records, validated against actual task reads. Frozen
  references remain excluded. Offline checks and publication to draft PR #7 are
  the implementation milestone; semantic evaluation/acceptance remains separate.
- On 2026-10-29 the user asked to examine how Synopsys builds these systems now,
  rather than treating it only as a future integration. Reviewed primary Synopsys
  architecture/demo material and a separate NVIDIA/Siemens evaluation account.
  The resulting proposal is in the roadmap/comparison, including the scope of a
  possible early SV-07 source audit. Vendor claims are not engineering acceptance;
  no model switch, manager agent, toolchain integration or new spending is implied.

- The corrected source-accounting condition at 6e01efc also failed before
  planning. Evidence IDs were valid, but two source blocks were both used as
  evidence and classified non-normative because they contained inline references;
  one also received a second disposition. Keep the guard and raw failure evidence.
  Raw extraction still loses source qualifiers and infers an unsupported conflict.
  Do not hand-edit the output into a passing run or proceed to a separate case.
  The next corrective work is offline: align disposition granularity with passages
  and distinguish missing relationship information from a proved contradiction.
  No new paid execution was scheduled. The 2026-10-29 decision above subsequently brought the limited SV-07 source audit forward.

- SV-05's first candidate failed exact-quotation validation before planning.
  The failure was retained without approximate matching or manual correction.
  The implementation correction precomputes source passages and supplies an enum
  of valid evidence IDs; Python copies original text/spans. Offline compatibility
  passed; draft/report V2 and prompt 10 were frozen and the separately declared
  corrected condition ran once with a $0.28 cap. Its failed outcome is recorded above.
  This changes evidence selection mechanics, not frozen semantic expectations.

- On 2026-10-28 the user approved SV-05: source-linked requirements with explicit
  conditions/values/exceptions and visible skipped/unresolved passages, followed
  by the frozen 13-label comparison on the same model/KB and a separate case only
  if the candidate improves without new unsupported behavior. Implement an opt-in
  bounded-packet trial with a versioned accounting artifact and unchanged V1 plan/
  analysis exports. Exact quotations establish location, not semantic completeness.
  No extra agent role, full-document rollout or SV-07 implementation in this slice.
  The remaining aggregate balance at that approval was $0.4391924945; no merge.

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

1. **SV-10 fixed-candidate measurement, approval pending:** one auditor-only
   condition is prepared under artifacts/evaluations/source-first-fixed-candidate-2026-10-31-v1/.
   It uses V2's accepted analysis/source/KB at code 719235c / prompt 14, capped at
   $0.20 / 12 calls. Execute its ignored execute.py once only after applicable
   user approval is recorded; --check passes without model calls. Approval/start
   files are absent. Source answers stay outside the run; no extraction or plan.
2. **SV-07 review:** draft PR #11 is published with all three checks passing on
   code head 719235c. Review schema and prompt-14 evidence rules. Keep the stack
   experimental until measured correction quality is useful; no merge yet.
3. **Quality gate:** measure all thirteen labels and every accepted finding,
   including false positives, supported advice and KB applicability. Schema
   success alone cannot promote the 6/13 extraction or approve automatic repair.
4. **Knowledge curation / SV-06:** use the
   [focused review guide](knowledge/REVISION_NOTES.md) to collect entry-specific
   engineer decisions and assess actual application. Preserve reference separation.
5. **SV-04 retrieval:** after the current correction/comparison, add cases for
   matches beyond character 1,000, Unicode coordinates and more than 12 hits; fix
   match-centered excerpts and stable pagination, then bounded neighbor/table
   context. Keep this separate from the bounded audit correction.
6. **Acceptance boundary:** no full-DOCX run, model migration or automatic repair
   is authorized by this milestone. Engineering signoff still needs the actual
   workload and reviewed references. A vendor comparison supplies design ideas,
   not acceptance evidence.

## Validation and result references

- 2026-10-30 source-first correction at f847788: 347 offline tests passed (91%
  coverage), Ruff check/format, strict mypy (49 files), source/wheel build and
  repository policy. This includes the 13 new CI policy regressions. Software
  validation is complete; paid measurement and engineering acceptance are pending.
- CI safeguards/foundation merges: all three checks passed on PR #9 head 247e389,
  #4 head 8434065, #5 head 3024648 and #6 head 02c551b before each merge. Updated
  drafts #7 eff6d84 and #8 d342406 also pass all three checks.
- Source-first PR #10: remote 97376fe verified and all three CI checks passed.
  Historical compatibility smoke check read all nine prior audits plus their
  original spend ledgers without model calls. Final handoff changes docs only.
- Original frozen source-first conditions (ignored local artifacts; now executed):
  `artifacts/evaluations/source-first-calibration-2026-10-30-v1/condition.json`,
  SHA-256 `26529fcdb0a85865eda26ca3e0e044da7d95b18fda33d9ff1d0b15a343e87486`;
  `artifacts/evaluations/source-first-real-2026-10-30-v1/condition.json`, SHA-256
  `f738c8ecdd9c84c83ee7c6f4e79f497d745805681af764763a6fcc1cfb3d07ed`.
  Both bind code 73d1ff3, prompt 13, GPT-5 mini / Azure Sweden, the unchanged
  KB/source/reference hashes and six turns per invocation. Calibration allows
  4,000 output tokens and the real packet 12,000. Real run ID is
  `27614aea-b0f3-4dff-98aa-d5ec17b73f57`; this attempt is interrupted before analysis.
  Calibration has 47 calls/$0.102234715 and zero reservations; real V1 has two
  attempts/$0.001897500 reported plus $0.136400000 unsettled. All receipts remain.
- Recovery V2 (approved 2026-10-31, execution/assessment in_progress):
  `artifacts/evaluations/source-first-real-2026-10-30-v2/condition.json`, SHA-256
  `19b40390b40607acd2112b102e4bef0535cd4c6ae2556d47058ebecefb704bea`;
  run `89fd1d82-7569-4c63-8ace-b6bba33face3`. Same runtime and inputs; zero calls.
  Storage probe passed with over 4 GiB free; repeat it immediately before a run.
- 2026-10-29 calibration implementation at 7be4ecb: 322 offline tests passed
  (91% coverage), Ruff check/format, strict mypy (48 source files) and source/wheel
  build. Four GitHub checks passed on Python 3.12/3.13. New checks cover complete
  input preflight, reference exclusion, shared budget/unknown charges, interruption
  recovery without retry, and constrained audit references. Final result documents
  do not change runtime; full local code checks were not repeated for them.
- Paid evaluation and provisional assessments are summarized in the
  [results](../evals/source-audit-results-2026-10-29.md). Calibration V1 failed;
  V2 completed eight cases; the real run completed extraction/audit only. Private
  assessments bind output/source/reference hashes and retain all cases/labels.
  Aggregate ledgers were reconciled, excluding duplicated review copies. No
  additional reservation, new plan, KB benefit claim or engineering acceptance.
- 2026-10-29 V3/audit implementation: 301 offline tests, 91% coverage; Ruff
  check/format, strict mypy (47 files), source/wheel build passed. Tests cover mixed
  passages, immutable attempts/feedback, forbidden obligation changes, exhausted
  corrections/budgets across resume, audit/KB reference validation, batch propagation,
  CLI analysis-only/resume and legacy/current exports. All four code-head CI
  checks passed at a51b67d. Verified 39 local documentation links/anchors, committed
  paths, wheel contents and credential/local-only exclusions. No paid execution occurred.
- Eight synthetic source-audit controls are frozen under
  artifacts/evaluations/source-audit-controls-2026-10-29-v1/. Manifest SHA-256:
  8ff807b195c5f8212535496d73066768afb6a565f5ee55c8571a3e684a67e1cb.
  Every source/analysis/accounting/reference binding was verified offline. Expected
  judgments are isolated in reference/ and remain agent_proposed; no detector score.
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

### 2026-10-28: Source accounting implemented; live candidates rejected

- Implemented opt-in source obligations, conditions/constraints/exceptions,
  proposed dispositions, exact source spans and visible unaccounted text. Immutable
  extraction/task receipts support resume; CLI/Excel show the bound report. One
  source chunk is supported; V1 analysis/plan and accounting readers remain usable.
- Quotation-based condition 789b26d failed before analysis acceptance on four
  altered quotations. Retained three calls and $0.023319923, zero unsettled.
  Replaced model-retyped quotes with enumerated passage selection and exact Python
  copying; froze draft/report V2 and prompt 10 at 6e01efc before the next call.
- Corrected condition 24f871cd-26dd-45ce-b72c-c326cdd451f1 failed before planning
  on incompatible dispositions after three calls and $0.031304306, zero unsettled.
  No accepted analysis/plan or separate-case validation. Both failed-run scores
  retain 13 unresolved obligations. Raw diagnostics also show semantic omissions
  and unsupported synthesis; the valid source IDs do not establish coverage.
- Passed 271 offline tests, Ruff check/format, strict mypy and source/wheel build.
  All four code-head CI checks passed. Original specialist instruction expressions
  match baseline exactly. Private inputs, labels, raw responses, assessments and
  ledgers stay under ignored artifacts/evaluations/source-accounting-2026-10-28-v1/
  and -v2/. The output is not ready for engineer handoff.
- Final reporting checks verified 28 local links/anchors, unchanged frozen runtime,
  source/KB/annotation/protocol hashes, and absence of tracked private paths or
  credential patterns. No new code tests were needed for these reporting edits.
- Published code at 6e01efc in draft PR #7 and verified the remote SHA. The review
  stack remains unmerged. Confirmed task charges are $0.3072733345 plus the old
  $0.308158400 uncertain reservation. No further paid run is scheduled. Next work
  is the offline correction described above; this does not complete SV-05.

### 2026-10-29: Immediate architecture comparison with Synopsys

- Studied GPT-Synopsys's announcement, AgentEngineer/Autopilot architecture and
  availability, the DV demonstration and reusable VIP collateral. Cross-checked
  the development method against NVIDIA/Siemens's artifact-verification account.
  Separated vendor claims, published mechanisms and our proposed adaptations.
- Compared these with current routing, KB procedures, source accounting and the
  rejected extraction. Recorded an interface mismatch, absent accounting feedback
  and absent pre-planning semantic audit. Existing durability, budgets and frozen
  evaluation contracts remain useful; a new manager model is not required.
- Added the source-backed comparison and roadmap proposal; current documents are
  local/uncommitted on feat/source-obligation-accounting at e638533. No runtime
  changes, inference, new allocation, code-test rerun, merge or publication.
- Documentation validation passed: 33 local links/anchors, whitespace checks,
  credential-pattern scan, documentation-only diff and local-only AGENTS.md.
- Next: review/finalize the proposed SV-05 correction and limited SV-07 audit
  contracts, including false-alarm controls, before implementing that expanded
  slice. The original aggregate budget and quality gates remain unchanged.

### 2026-10-29: Passage feedback and pre-planning source audit

- User authorized updating the tickets and implementing the researched slice.
  Updated SV-05/SV-07 acceptance scope, implemented V3 passage dispositions and
  persistent structured feedback with one disposition-only correction, and retained
  V1/V2 report readers. Corrected drafts cannot alter obligations or gaps.
- Reused the reviewer role for a source audit before planning. Typed source findings
  and proposed KB application records validate references and task-specific reads.
  Audit suggestions remain advisory, visible in planning/export and final status.
  Added analysis-only execution and offline CLI inspection; no additional agent.
- Passed 301 offline tests (91% coverage), Ruff check/format, strict mypy (47 files)
  and source/wheel build. Verified normal specialist instructions unchanged. Eight
  synthetic controls and isolated expectations were frozen and hash-checked locally.
  Model quality, knowledge benefit and engineering acceptance remain unmeasured.
- Published implementation, research comparison and docs at a51b67d in draft
  PR #7, verified its remote SHA directly and confirmed all four code-head CI
  checks passed. Updated the PR title/body to the final scope. Final handoff edits
  are documentation only. No merge or new paid run; charges/reservations unchanged.
  Next: technical review and offline calibration runner, then a declared capped
  condition before any inference. Model quality remains an open acceptance gate.

### 2026-10-29: Auditor calibration and real extraction comparison

- Implemented SV-10's frozen-candidate runner with offline preparation/status,
  exact input/configuration bindings, one shared cost/call ledger and terminal
  outcomes that do not silently retry after failure or interruption. The runtime
  and runner share the same audit executor. Published a9c482f in draft PR #8.
- First live condition failed on block IDs in passage references. Preserved its
  rejected output and all eight outcomes. Corrected model-selected reference
  enums and audit instructions in prompt 12, keeping source-audit-v1 fields and
  historical readers. Published 7be4ecb after 322 offline tests, Ruff, strict mypy
  and build passed; verified the remote SHA and all four code-head CI checks.
- Separately froze and ran the correction inside the original calibration cap.
  All eight cases completed: 4/5 defects flagged, 3/5 supported corrective actions,
  0/3 valid-control false alarms. Whole-obligation omission remained undetected;
  relabeling an unsupported relationship was not a safe correction. Judgments
  remain agent_proposed and this development set is not a blind benchmark.
- The real packet completed extraction/audit in analysis-only mode. Provisional
  coverage is 9/13, matching baseline with two recoveries and two regressions;
  audit detected none of four incomplete labels. Inspected all four KB applications,
  finding both useful transfer and unsupported applicability. No planner ran.
- This milestone used 33 calls/$0.112424411 with no new reservation. Aggregate
  confirmed/uncertain totals and remaining original allowance are in Current state.
  Private assessment hashes/paths and safe aggregate results are in the linked
  results document. Source excerpts, reference answers and generated outputs remain
  ignored. The public handoff is documentation only in PR #8; nothing merged.
- Handoff checks passed: 31 local documentation links/anchors, whitespace checks,
  credential-pattern scan and verification that AGENTS.md/private artifacts remain
  ignored and untracked. Full local code checks were not repeated for these docs.
- Recorded the next SV-07 correction and stage-specific SV-10 assessment boundary
  in the roadmap. Keep audit advisory and the full-planning gate closed. Next:
  source-first omission review and evidence-supported correction requests offline,
  then a separately declared comparison only after checks and applicable allocation.

<!-- At each milestone/handoff, update the current sections and append an entry:
Date and milestone; ticket/substep status; changes and safe evidence links;
checks actually run and outcomes; decisions/authorization; blockers and scope;
ordered next action. Include commit/PR references only when they exist.
-->

### 2026-10-30: Merge safeguards prepared

- Added a required-ready repository-policy job, tracked-file/credential checks,
  prompt-version comparison and PR evidence template. PR/main CI replaces
  duplicate push/PR runs, with superseded runs cancelled. No application behavior
  changed; normal checks stay offline.
- Passed 215 offline tests (13 new policy regressions, 90% application coverage),
  Ruff check/format, strict mypy (40 source files), source/wheel build, index-policy
  and whitespace checks. Regressions reject private paths, redact credentials,
  avoid following symlinks/reading untracked files, and detect unversioned prompts.
- Next: publish/review this PR, require its three successful checks on main with
  resolved conversations and no force push/deletion, then merge reviewed #4–#6
  in order. No additional paid execution. The source-first audit correction follows
  on its own branch; #7/#8 remain draft.

### 2026-10-30: Safeguards merged; curation merge review

- PR #9 merged at 4458169; remote main SHA verified. Required checks are bound to
  GitHub Actions: repository-policy and quality on Python 3.12/3.13. Main requires
  the current base, PRs and resolved review threads; admin bypass, force pushes
  and deletion are disabled. Approval count is zero for the single maintainer.
- Reviewed PR #4's four engineering comments against revision notes; all map to
  proposed changes and remain pending engineering confirmation. Only public review
  documents are introduced. Updated this branch by merge, preserving frozen history.
- Next: merge #4 after final-head CI, then update/review/merge #5 and #6 in order.

### 2026-10-30: Curation merged; connector merge review

- PR #4 merged at e78e2ea after all three required final-head checks passed.
  The engineering comments are reflected in revision notes; entries remain proposed.
- Reviewed PR #5's frozen KB bindings, source/knowledge separation, forced tool
  consultation, OpenRouter response handling, legacy paths and regression tests.
  No blocking finding. Known guidance applicability/quality limits remain visible.
- Merged protected main into the connector branch. Only progress history required
  conflict resolution; no runtime content was changed by the merge. Next: final-head
  CI and merge #5, then documentation-only #6.

### 2026-10-30: Connector merged; evaluation record merge review

- PR #5 merged at 69ac52d after all three protected checks passed on 3024648.
  KB use is explicit/opt-in for proposed entries; no content became engineer-approved.
- Verified PR #6 has no source, test or dependency delta from its PR #5 base. Its
  rejected prompt trial remains reverted. Merged current main into this branch;
  only progress required conflict resolution. Next: merge #6 after required CI, then
  continue the source-first audit correction with historical evidence preserved.

### 2026-10-30: Foundation merges complete

- PR #6 merged at 9447b33 after required CI passed on 02c551b. Remote main verified.
  #4/#5/#6 are merged; #7/#8 remain experimental drafts. Carried safeguards and the
  merged foundation into #7 without rewriting history or altering its runtime.
- Next: propagate this base through #8 and finish/test the independent source-first
  inventory/comparison correction on feat/source-first-audit. No paid run started.

### 2026-10-30: Calibration branch aligned with protected main

- Propagated the merged foundation and CI safeguards through draft #7 and #8 with
  merge commits, preserving frozen code provenance and paid-result evidence.
  All four authorized merges (#9, #4, #5, #6) passed their exact-head required checks.
- Next: complete and publish source-first audit correction on feat/source-first-audit.
  Detailed experimental results remain unchanged; no new paid inference.

### 2026-10-30: Source-first omission review implemented

- Added source-inventory-v1 with exactly one reading per source passage. The
  inventory task can access source/KB only; a separate comparison binds it to the
  candidate and produces the existing source-audit-v1 projection. Both task
  receipts persist, validate lineage and recover without repeating completed work.
- Prompt 13 preserves qualifiers, treats skipped/cited passages independently and
  requires source-supported correction advice. Existing model/default settings,
  opt-in boundary and historical audit/export/spend access are retained.
- Passed 347 offline tests, 91% coverage, Ruff check/format, strict mypy (49 files),
  source/wheel build and index policy on integrated code f847788. All nine prior
  audits and their spending records also passed a local compatibility read. No paid calls;
  synthetic mocked outputs establish contracts, not improved auditor quality.
- Published [PR #10](https://github.com/noobjam/Project-x/pull/10) at 73d1ff3,
  verified remote SHA and all three CI checks. Synced local main to merged 9447b33.
  Frozen the unchanged eight controls and one analysis-only real condition locally;
  their hashes/settings are recorded above. No reference answers entered a run.
- Requested explicit approval for the $0.25 + $0.24 caps and $1.25 aggregate ceiling;
  approval is pending. Next: run/assess the controls only after that decision, then
  the real diagnostic if usable. Prior quality results and uncertain charges remain intact.

### 2026-10-30: Source-first comparison authorized and started

- User approved the prepared $0.49 comparison and $1.25 aggregate ceiling.
  Recorded separate immutable authorization receipts outside agent inputs.
- Rechecked both condition hashes, unchanged runtime/source/KB bindings, zero
  initial ledger calls and final-head CI on 97376fe. No offline code tests rerun;
  this milestone executes the already validated frozen candidate on the same branch.
- Calibration is active first; assess it before the conditional real run. Keep
  controls/labels fixed, prior failures charged and old uncertain reservation intact.

### 2026-10-30: Source-first calibration assessed; real diagnostic started

- Eight controls completed in 47 calls for $0.102234715, with zero unsettled
  reservations. Every seeded defect was detected (5/5, previously 4/5); four have
  a fully supported primary correction and one has mixed advice. Three valid
  controls remain free of false alarms. Count the three unsupported extra findings
  and one duplicate separately; this is not an automatic acceptance/repair gate.
- The independent readings retained the twelve control passages' explicit facts.
  Some inventory reasoning still invents a need for optional elaboration. Findings
  also confuse valid block references with passage IDs; retain this defect evidence.
- Provisional private assessment is at source-first-calibration-2026-10-30-v1/
  reference/assessment.v001.json (under ignored artifacts/evaluations), SHA-256
  0741896d0b34f6e65063a8b6800b4c898ece4a460d0908a75b0fa4a41f75d8c1.
  It permits only the already approved diagnostic real extraction/audit condition.
- Next: complete that condition under $0.24 / 24 calls and assess all thirteen
  labels plus every audit finding. No planner, code edit or automatic repair.

### 2026-10-30: Disk interruption retained; recovery prepared

- Real V1 stopped with exit 120 while the filesystem reported ENOSPC. No analysis,
  audit or plan completed; two requests were reserved, one settled at $0.0018975,
  and the second remains uncertain at $0.1364. After freeing space, the supervisor
  wrote an interrupted outcome without inventing the worker's missing response.
- Removed rebuildable project caches and the obsolete merge-worktree environment.
  Source, the active environment and all private evidence remain intact. Space
  recovered above 4 GiB and a write/fsync probe passed. Runtime code did not change.
- The configured inference key cannot query analytics metadata (HTTP 403); retain
  both old and new uncertain reservations. Do not change retention/logging settings.
- Prepared recovery V2 with the same inputs/runtime, capped at $0.24 / 24 calls.
  Including the full uncertain reservation, it fits the previously approved $0.49
  comparison/$1.25 aggregate ceilings. Requested explicit reallocation/retry
  approval; it remains pending. Safe results and next actions are published in
  PR #10 at c95c708; remote SHA verified. The recovery entrypoint is retained
  locally outside model inputs with a fresh storage check and space reserved for
  a terminal record. No fresh real score or engineering-ready plan is claimed.

### 2026-10-31: Real recovery authorized

- User approved the prepared $0.24 / 24-call V2 recovery within existing comparison
  and aggregate ceilings. Recorded an immutable authorization receipt outside the
  model inputs; retain the interrupted V1 charge/reservation and calibration results.
- Rechecked frozen condition/entrypoint/runtime hashes, zero prior V2 calls and
  all three CI checks on 0e68723. Approximately 2.8 GiB is free; the entrypoint
  repeats a write/fsync preflight and reserves space for its final outcome record.
- Active milestone is SV-10 on feat/source-first-audit. Run and inspect all thirteen
  labels at the existing frozen settings before deciding the next correction.

### 2026-10-31: Recovery failed inventory; all extraction labels assessed

- Executed the explicitly approved V2 once at frozen code 73d1ff3 / prompt 13.
  Storage preflight passed. Six calls cost $0.046524588 reported, with no new
  reservation. V1's $0.136400000 uncertainty remains reserved.
- Extraction completed and retained 6/13 labels. Compared with the original
  baseline there are two recoveries/five regressions; compared with the previous
  run, one recovery/four regressions. A covered label still has incomplete
  citations. All judgments are provisional and private evidence stays ignored.
- The response lists all 62 passage IDs once, but 17 context readings carry facts
  forbidden by host validation. The schema did not expose that constraint.
  Offline replay reproduces the rejection. No accepted inventory, comparison
  audit or plan exists; no detection score or quality promotion is claimed.
- Private assessment SHA-256:
  3ed6ff6f97215de946a133120fc3cde93a14a8f8dfa1b127dd41d6e06a4c1939.
  Safe aggregate results are in evals/source-first-results-2026-10-30.md.
- Next: focused offline SV-07 schema/prompt correction, regression checks and
  reviewable publication. New paid execution requires a declared allocation;
  remaining allowance is not an automatic retry. No code tests rerun for this
  results-only checkpoint.

### 2026-10-31: Inventory contract correction validated offline

- SV-07 focused follow-up on fix/source-inventory-contract, based on published
  results 2d104ec. Generation-only reading variants now encode existing context
  and behavior fact-list rules. Persisted v1 readers and validation are unchanged.
- Prompt 14 clarifies context descriptions, field-specific citation namespaces,
  evidence-bound repair advice and one finding per root cause. The analyst is
  unchanged. No extra agents, automatic repair or fallback inference was added.
- The regression failed against the old outgoing schema, then passed through the
  actual SDK/transport. 354 offline tests pass (91% coverage), Ruff/format,
  strict mypy (49 files) and build pass. Eight saved prompt-13 calibration audits
  were read successfully with their original evidence/knowledge receipts.
- This is technical completion only. No new paid call or engineering acceptance.
  Publish the focused draft, then prepare a $0.20 / 12-call auditor-only condition
  against the fixed accepted V2 analysis. Approval is still required for that
  condition; the prior one-attempt recovery authorization is consumed.

### 2026-10-31: Correction published; fixed-candidate condition prepared

- Draft PR #11 targets #10. Code commit
  719235c9a9ded4f6fc1e729968783308b9558bf7 is published; remote SHA verified.
  repository-policy and Python 3.12/3.13 quality checks all passed on this head.
  PR #10's results head 2d104ec also passed all three checks. Neither was merged.
- Prepared a new auditor-only condition using the exact accepted V2 candidate,
  source, accounting and KB, with prompt 14. No reference answers are in its
  input bundle or run. The run has zero model calls and no authorization/start
  marker. Runtime/input/budget/storage preflight passes with execute.py --check.
- Proposed cap $0.20 / 12 calls leaves both existing total ceilings intact.
  The user must approve this new condition before execution; the previous recovery
  authorization covered one attempt. Do not rerun extraction or claim its 6/13
  score improves merely because the auditor identifies omissions.
- Next after approval: run the frozen condition once, assess inventory and every
  finding against all thirteen labels, record misses/false findings/advice quality,
  then decide the narrow correction to extraction. No automatic repair or plan.
