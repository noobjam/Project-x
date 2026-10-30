# SV-05 bounded source-accounting trial

The user approved this experiment after the model screen and rejected prompt-only
trial described in [the results](quality-results-2026-10-28.md). It targets source
omissions and loss of conditions, constraints and exceptions before planning.

## Frozen intervention

Compare the retained GPT-5 mini / Azure Sweden source-accounting-off condition
with the opt-in structured extraction workflow. Keep the same source packet,
knowledge snapshot, proposed-entry opt-in, model/provider, generation limits and
revision limit. The planner/reviewer instructions remain byte-identical. The
intervention bundles the analyst contract/instructions, deterministic fact
projection and visible accounting gaps in downstream inputs. It does not isolate
individual fields or promise semantic correctness from valid source quotations.

New formats are source-accounting-draft-v1 and source-accounting-v1; runtime prompt
version is 9. This bounded experiment adds no agent role and accepts one source
chunk. The normal V1 analysis/plan export contracts remain supported. Accounting
is disabled by default pending evidence and review.

Reuse the exact frozen 13-label annotations and scoring criteria from the earlier
development comparison. Preserve compound-label denominators, partial-coverage
notes, disputed/unresolved judgments and failures. Do not feed annotations or
reference answers to any specialist. Assess extraction, plan adequacy and review
separately; more rows or quoted bytes do not earn semantic coverage credit.

Inspect whether each recovered condition/exception is actually source-supported,
whether an unaccounted passage is visible, and whether non-normative dispositions
hide real obligations. Check downstream unsupported behavior and false findings;
do not hide regressions behind an extraction score. All judgments remain
agent_proposed until engineering review.

## Execution and decision

Freeze code/configuration/source/knowledge/annotation hashes before inference.
The first candidate has a $0.28 maximum within the original $1 aggregate task cap.
Before it starts, prior confirmed charges are $0.2526491055 and a separate
$0.308158400 reservation remains uncertain. Include every failure and remaining
reservation; do not renew allocations silently. No automatic workflow retry.

If the candidate improves extraction without new unsupported behavior, validate
a separate development packet with existing frozen labels and an explicit
allocation from the then-remaining balance. That case is not blind gold. If the
candidate fails or regresses, retain the result, keep the feature experimental
and record the next corrective decision before more paid work. No full-DOCX run,
model promotion, merge or engineering handoff is authorized by this experiment.

## Corrected condition: passage selection

The first condition at 789b26d stopped before planning after three calls costing
$0.023319923: four model-retyped quotations did not match source text. Two involved
Unicode corruption and two altered or mixed source passages. No analysis was
accepted; no workflow retry was made. Preserve this failed attempt in results.

The next candidate replaces model-retyped quotations with selection from
precomputed passage IDs. Python splits paragraphs mechanically at sentence/line
boundaries, retains whole table rows and supplies exact source text/spans. The
output schema restricts evidence IDs to the supplied set. This changes the analyst
input/output representation, not its semantic obligations or evaluation labels.
Draft/report version 2 and prompt version 10 record that change; V1 accounting
remains readable. Preserve all earlier comparison conditions and costs.

Freeze this corrected condition before one new $0.28-capped execution. Prior
confirmed spending is now $0.2759690285, with $0.308158400 still uncertain;
$0.4158725715 remains under the same $1 aggregate cap. The source, model/provider,
KB, planner/reviewer instructions, generation limits and 13-label inventory remain
fixed. A valid selected ID proves location, not support or complete extraction.

## Results

Both accounting conditions were rejected before planning. The corrected passage-ID
condition resolved quotation corruption, but it did not establish usable extraction
or improved plans. Keep the feature disabled by default and the PR in draft.

| Condition | Outcome | Calls | Reported cost | Frozen-label result |
| --- | --- | ---: | ---: | --- |
| Saved GPT-5 mini baseline | Complete; quality insufficient | 16 | $0.081798244 | 9/13 fully extracted; 2/13 fully adequate scenarios |
| Quotation-based accounting, 789b26d | Failed exact-source validation | 3 | $0.023319923 | All 13 unresolved; no accepted analysis |
| Passage-ID accounting, 6e01efc | Failed disposition consistency | 3 | $0.031304306 | All 13 unresolved; no accepted analysis |

Neither new run has an unsettled charge. Both failures remain in the evaluation;
raw output is diagnostic material, not a completed candidate scored as successful.
The baseline's partial coverage and unresolved judgments remain in the prior report.

The corrected analyst selected valid source IDs, but classified two evidence-bearing
blocks as non-normative because they contained informative cross-references. One
block also received a second disposition. The validator rejected these assignments.
Inspection of the rejected extraction still found omitted qualifiers and an
unsupported conflict claim between separate mechanisms. Selecting a passage did
not ensure that every fact in it survived extraction.

The next correction should first address mixed normative/informative passages and
conflict judgments with offline counterexamples. Preserve exact evidence checks;
do not hand-edit a model response into an accepted run. No separate-case or
full-document execution is justified by these results, and no further paid run is
scheduled. All quality observations remain agent_proposed.

Technical validation at 6e01efc: 271 offline tests passed (91% coverage), Ruff check/
format, strict mypy and source/wheel build passed; all four GitHub code-head checks
passed on Python 3.12/3.13. Draft [PR #7](https://github.com/noobjam/Project-x/pull/7)
is stacked on #6. These checks do not establish engineering-quality acceptance.

Current aggregate: $0.3072733345 reported plus $0.308158400 still uncertain from an
earlier attempt; $0.3845682655 remains under the original $1 ceiling. Private
experiments, source, assessments and ledgers remain in ignored artifacts/evaluations/
source-accounting-2026-10-28-v1/ and -v2/. No source excerpts or generated plans are
published with this report.
