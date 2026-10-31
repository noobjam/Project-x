# Source-first auditor calibration and failed real recovery

The independent source reading recovers the previously missed synthetic omission:
all five seeded defects are now detected. The auditor still emits unsupported
extra findings and mixed correction advice. After an initial disk interruption,
the approved real recovery completed extraction but failed inventory validation.
Extraction covers 6/13 frozen labels, down from 9/13. No real audit comparison or
engineer-ready plan was produced.

These are provisional development judgments, not engineering acceptance or a
held-out benchmark. The [protocol](source-audit-protocol.md) and
[previous results](source-audit-results-2026-10-29.md) remain unchanged evidence.

## Conditions and spending

Code 73d1ff3 / prompt 13 adds an independent source/KB inventory followed by a
separate comparison with the candidate. Runtime source is unchanged from the
validated PR #10 implementation. The same eight controls, real source packet,
reference labels, KB snapshot and GPT-5 mini / Azure Sweden endpoint were retained.
Calibration allows 4,000 output tokens per call; the real packet allows 12,000.
Both use six turns per invocation. No planner or semantic repair ran.

The user approved $0.25 / 96 calls for calibration and $0.24 / 24 calls for the
conditional real diagnostic, with a $0.49 combined allowance and $1.25 aggregate
ceiling. Failure does not silently renew an allocation.

| Condition | Outcome | Calls | Provider-reported charge | Unsettled reservation |
| --- | --- | ---: | ---: | ---: |
| Source-first calibration | All eight audits completed | 47 | $0.102234715 | $0 |
| Real analysis-only V1 | Interrupted before analysis; process exit 120 | 2 | $0.001897500 | $0.136400000 |
| Real recovery V2 | Extraction completed; inventory rejected | 6 | $0.046524588 | $0 |
| This comparison so far | Both failures retained | 55 | $0.150656803 | $0.136400000 |

The outstanding reservation is a conservative bound, not a confirmed charge.
The interrupted request has no saved provider response or generation ID. A
read-only analytics metadata request returned HTTP 403 with the configured key;
no settlement was inferred. OpenRouter's broader analytics lookup requires a
[management key](https://openrouter.ai/docs/api/api-reference/analytics/get-available-analytics-metrics-and-dimensions).
No logging policy or credential configuration was changed.

## Calibration assessment

| Measure | Previous auditor | Source-first auditor |
| --- | ---: | ---: |
| Seeded defects detected | 4 / 5 | 5 / 5 |
| Defects with a fully supported primary correction | 3 / 5 | 4 / 5 |
| Valid controls with false alarms | 0 / 3 | 0 / 3 |
| Unsupported extra findings on defective controls | 0 | 3 |
| Duplicate findings | 0 | 1 |
| Unassessed controls | 0 / 8 | 0 / 8 |
| Calls | 24 | 47 |
| Provider-reported charge | $0.058390849 | $0.102234715 |

Every one of the nine current findings was assessed. Two unsupported findings
mistake valid block references in the existing analysis/accounting contracts for
missing passage references. A third asks for optional detail absent from both
source and candidate, and overstates that absence as an extraction problem.
Another finding duplicates an already detected defect. These issues must remain
visible alongside the zero false-alarm count on the three valid controls.

The previously missed whole omission is now detected despite its incorrect
non-normative disposition. Independent readings retain the explicit facts in all
twelve supplied control passages. Inventory explanations can still manufacture a
need for extra detail and influence the later comparison; passage accounting is
not a semantic correctness guarantee.

One detected unsupported relationship still receives mixed advice: an unresolved
outcome is acceptable, but the alternative derivation has not established all
required shared reference/clock assumptions from the supplied source. It is not
an approved automatic repair. Three KB application spot-checks also show that a
useful generic lesson does not establish all prerequisites of its full procedure.
All KB reads were validated mechanically; KB benefit was not measured.

This is evidence of improved omission detection on a small development set,
with higher cost and remaining noise. It does not establish general accuracy,
automatic repair safety or a better real verification plan.

## Real comparison and recovery

The eight completed controls were usable for a bounded real diagnostic, so the
already approved real condition started. The Mac then reported `ENOSPC`; the
worker exited with code 120 without completing analysis or writing its final
status. The supervising session recorded an interrupted outcome after recovering
space. All original call/reservation files remain intact; no artifact was edited
into a successful result. All thirteen real reference labels remain unassessed
for this attempt. The last completed real extraction result is still 9/13.

Removed only rebuildable project caches and the temporary merge worktree's Python
environment. Private inputs, references, outputs, source and the active environment
were preserved. Disk availability subsequently recovered to more than 4 GiB,
and a write/fsync probe passed. A future paid start must recheck space immediately.

The user explicitly approved recovery V2 on 2026-10-31: unchanged
code/prompt/input/KB and generation settings, at most $0.24 / 24 calls, reusing
unused calibration allowance. Storage preflight passed. The run completed
extraction, then stopped with ModelResponseError during inventory validation.
All six calls settled at $0.046524588; this failure added no uncertain reservation.

Offline replay of the saved response found all 62 expected passage IDs exactly
once, valid JSON and a normal stop. Seventeen context readings included descriptive
facts. The persisted contract requires an empty fact list for context, but the
model-facing schema allowed those lists and the prompt did not state the rule
explicitly. Host validation correctly rejected them; no response was edited into
an accepted inventory. The comparison invocation and planner never ran.

All thirteen frozen extraction labels were assessed from the accepted analysis:

| Measure | Original baseline | Previous real run | Recovery V2 |
| --- | ---: | ---: | ---: |
| Fully retained compound labels | 9 / 13 | 9 / 13 | 6 / 13 |
| Incomplete or absent labels | 4 / 13 | 4 / 13 | 7 / 13 |
| Labels unassessed | 0 | 0 | 0 |

Against the original baseline, two labels recover and five regress; against the
previous real run, one recovers and four regress. One covered label has incomplete
citations despite its facts appearing in the source; coverage does not establish
complete support. Optional clarification and an unestablished source-conflict
claim also remain. The analyst instruction is unchanged; a single sample does not
explain the variation, and the later auditor did not cause upstream omissions.
There is no real audit detection/false-alarm score because comparison never ran.
Rejected inventory facts receive no accepted-coverage credit. KB benefit remains
unmeasured. Detailed judgments and source evidence stay in the ignored reference
directory.

## Decision and next actions

Keep PR #10 experimental and the auditor advisory. The recovery authorization is
consumed; preserve both failed attempts and the outstanding reservation. Complete
the offline correction before proposing another paid condition. No full planning,
additional case or automatic semantic repair is authorized.

The next SV-07 correction must expose the existing classification/fact-list rules
in the model-facing schema without weakening validation. It should also distinguish
block IDs in analysis from passage IDs in audit evidence, suppress duplicates,
separate optional source elaboration from extraction defects, and remove
unsupported repair alternatives.
Use the existing controls as regressions and measure on the real source before
promoting the workflow. Preserve the frozen runtime and receipts for both attempts;
new code is a new condition, not a resume of the failed inventory.

## Offline corrective follow-up

The focused fix/source-inventory-contract branch implements prompt 14. Its
generation schema exposes the existing behavior/context fact-list constraints as
separate alternatives, while persisted v1 contracts and host validation keep their
meaning. Instructions clarify context-only descriptions, block versus passage
citations, one finding per root cause, and source-supported correction requests.
The analyst, model, KB and automatic-repair policy are unchanged.

A regression using the actual SDK and gateway request path failed on the previous
schema and passes with the fix. All 354 offline tests pass (91% coverage), as do
Ruff, strict mypy and build. All eight saved prompt-13 calibration audits remain
readable with their original inventory/KB receipts. This establishes software
compatibility, not better model judgment; prompt 14 has not been evaluated live.

The proposed next measurement reuses the accepted V2 analysis and source snapshot
and runs only the corrected independent inventory and comparison. It would assess
all seven incomplete labels, all thirteen labels overall, citation support and
every finding without buying another extraction. Its maximum proposed allocation
is $0.20 / 12 calls, inside both existing total ceilings with all uncertain
reservations retained. It requires a new applicable approval before execution.

## Provenance and validation

Ignored local roots under `artifacts/evaluations/`:

- `source-first-calibration-2026-10-30-v1/`
- `source-first-real-2026-10-30-v1/` (interrupted)
- `source-first-real-2026-10-30-v2/` (approved; failed inventory after extraction)

Calibration assessment: `reference/assessment.v001.json`, SHA-256
`0741896d0b34f6e65063a8b6800b4c898ece4a460d0908a75b0fa4a41f75d8c1`.
The original condition hashes remain in [progress](../docs/progress.md).
Recovery condition SHA-256:
`19b40390b40607acd2112b102e4bef0535cd4c6ae2556d47058ebecefb704bea`;
run ID `89fd1d82-7569-4c63-8ace-b6bba33face3`.
Recovery assessment: `reference/assessment.v001.json`, SHA-256
`3ed6ff6f97215de946a133120fc3cde93a14a8f8dfa1b127dd41d6e06a4c1939`.

The prior implementation passed 347 offline tests (91% coverage), Ruff,
strict mypy, build and Python 3.12/3.13 CI. Those tests were not rerun for this
results-only milestone. Current checks validate the frozen conditions, all audit
receipts, full finding inventory, unchanged references, ledgers and safe publication.

Aggregate provider-reported charge is now $0.5703545485, with $0.444558400
reserved ($0.308158400 historical plus $0.136400000 from the interrupted run).
Combined commitment is $1.0149129485 under the approved $1.25 ceiling. This
comparison's commitment is $0.287056803 under its $0.49 ceiling. No uncertain
charge has been released; unused allowance is not an automatic new condition.
