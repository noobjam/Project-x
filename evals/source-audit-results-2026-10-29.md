# Source audit calibration and real-packet result

The source-accounting workflow now completes extraction and audit on the bounded
real packet, but it has not improved extraction quality over the retained baseline.
The auditor misses omissions and cannot yet serve as an acceptance gate.

These are provisional development judgments, assessed against frozen references
outside agent retrieval. They are not engineering approval or a held-out benchmark.
The execution protocol is [recorded separately](source-audit-protocol.md).

## Conditions and outcomes

All conditions used GPT-5 mini through OpenRouter's Azure Sweden endpoint and the
same frozen KB. The corrected candidate is code 7be4ecb, prompt 12. Calibration
allows 4,000 output tokens per call; the real packet retains 12,000. No planner,
automatic semantic repair or full-document evaluation ran in this milestone.

| Condition | Execution | Calls | Provider-reported cost | Unsettled reservation |
| --- | --- | ---: | ---: | ---: |
| Calibration V1, code a9c482f / prompt 11 | First case rejected; seven unrun | 3 | $0.009409950 | $0 |
| Calibration V2, code 7be4ecb / prompt 12 | Eight audits completed | 24 | $0.058390849 | $0 |
| Real packet, analysis only, code 7be4ecb / prompt 12 | Extraction and audit completed | 6 | $0.044623612 | $0 |
| This milestone | All failures retained | 33 | $0.112424411 | $0 |

V1 used block IDs where passage IDs were required. Its raw diagnostic also
mistook optional KB checklist detail for missing extracted facts. V2 constrains
references in the response schema and narrows the audit to extraction fidelity.
The failed condition remains unchanged; it is not counted as an accepted audit.
V2 was separately frozen with a $0.19 / 45-call limit, keeping both calibrations
within the original $0.20 / 48-call allocation. The real condition stayed within
its separate $0.18 / 18-call allocation.

## Calibration quality

| Measure | Corrected condition |
| --- | ---: |
| Seeded defects flagged | 4 / 5 |
| Seeded defects with fully supported corrective advice | 3 / 5 |
| Valid controls with false alarms | 0 / 3 |
| Unassessed controls | 0 / 8 |

The auditor missed a complete obligation that the candidate wrongly classified
as non-normative. It detected an invented timing relationship but recommended
relabeling it as derived, which does not establish the missing relationship.
A KB application spot-check also found a conflict-handling procedure marked
applicable only because a conflict might arise later. Actual reads are recorded;
they do not prove correct application. The full calibration application inventory
was not semantically assessed.

These eight controls informed development, including the correction after V1.
The small valid set does not establish a general false-alarm rate.

## Real-packet quality

| Measure | Retained baseline | Current analysis-only candidate |
| --- | ---: | ---: |
| Fully extracted provisional obligations | 9 / 13 | 9 / 13 |
| Previously missed labels recovered | — | 2 |
| Previously covered labels lost | — | 2 |
| Remaining incomplete labels detected by the new auditor | Not run | 0 / 4 |
| Adequate plan scenarios | 2 / 13 | Not evaluated; no plan generated |

All thirteen labels remain in the denominator. Partial extraction does not earn
full-label credit. The candidate contains one unsupported broadening of a source
condition. Its sole audit finding raises a potentially useful context question
but also alleges inconsistency without establishing that the statements concern
the same path and condition. It identifies none of the four incomplete labels.

All four real-packet KB application records were inspected. One transfers a
methodology appropriately, one over-applies a check without a defined target
contract, one asserts applicability without establishing its prerequisite, and
one is only partly supported by its cited passages. No KB-benefit comparison or
engineering editing-time measurement was performed.

The analysis-only stage succeeded technically. Its private stage-specific
assessment validates source/reference hashes and every label-to-requirement link;
it does not label a run without planning as full-workflow completion. Compound
judgments, support reviews and output hashes remain in ignored local artifacts.

## Decision and next work

Keep the candidate opt-in and the audit advisory. The quality gate for full
planning or a separate real case is not met. Retain the baseline and every failed
condition; this result provides no evidence for promoting the candidate, changing
models or claiming a cost saving.

The next bounded correction is SV-07 source-first omission review: inspect the
source independently of the analyst's chosen requirements and dispositions, then
compare the two. Include wholly skipped passages and lost qualifiers inside cited
passages. Require evidence for suggested corrections; changing a claim's label
does not make it supported. Optional source elaboration must stay distinct from
an extraction defect. Use the existing reviewer role and measure calls/output
before expanding the workflow. See [ticket scope](../docs/agent-roadmap.md#sv-07-add-typed-review-findings-on-existing-plans)
and the ordered [handoff](../docs/progress.md#next-moves).

Software validation at code 7be4ecb: 322 offline tests passed, 91% coverage, Ruff
check/format, strict mypy on 48 source files, source/wheel build and all four
GitHub CI checks on Python 3.12/3.13. This results handoff changes documentation
only. Software checks do not establish semantic acceptance.

## Local provenance and aggregate budget

Private inputs, outputs and judgments remain under these ignored roots:

- `artifacts/evaluations/source-audit-calibration-2026-10-29-v1/`
- `artifacts/evaluations/source-audit-calibration-2026-10-29-v2/`
- `artifacts/evaluations/source-audit-real-2026-10-29-v1/`

The real assessment is `reference/assessment.v001.json` in the last root, SHA-256
`769802d681cad6253242d7239a3ccbd5d17338ce0482117f9294641ab6957d1d`.
Its run is `0050f3ac-afa9-4438-9bd9-ece09a94aab1`.

Ledger reconciliation totals $0.4196977455 provider-reported and $0.308158400
still reserved for an older uncertain request. The $0.7278561455 combined
commitment leaves $0.2721438545 under the original $1 task ceiling. Unused balance
does not renew an experiment allocation. No further paid run is scheduled.
