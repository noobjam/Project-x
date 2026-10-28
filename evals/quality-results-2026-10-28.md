# Development model screen — 2026-10-28

The connected workflow remains unsuitable for engineering handoff. Changing the
model improved requirement extraction in this development case, but did not
produce a sufficiently grounded plan or reliable review. No model is promoted.

The [protocol](quality-comparison.md) was committed at 54493b8 before inference.
Runtime source, dependency versions, input packet and knowledge snapshot matched
the saved baseline. The declared change was the model/provider bundle. Reasoning
and sampling defaults were not normalized across providers. Both conditions used
the actual KB tools with proposed entries explicitly enabled and no repair loop.

| Measurement | Gemini 3.1 Flash Lite / Google EU | GPT-5 mini / Azure Sweden |
| --- | --- | --- |
| Fully extracted obligations | 2/13 | 9/13 |
| Fully adequate scenarios against those obligations | 0/13 | 2/13 |
| Unresolved scenario judgments | 0 | 1 |
| Unsupported output items / assessed inventory | 2/11 | 7/32 |
| Unresolved output support | 1/11 | 5/32 |
| Calls in completed workflow | 9 | 16 |
| Provider-reported completed-workflow charge | $0.0192188975 | $0.081798244 |

These are **agent-proposed judgments**, not engineer-approved scores. Thirteen
source-bound labels were frozen before the alternative output. Several labels
contain multiple necessary conditions; partial matches do not earn full credit.
Both outputs contain useful partial checks. Unsupported-item counts combine
requirements and plan items, whose number and granularity differ; they are not
atomic-claim error rates. Detailed partial matches and rationales remain private.

The reviewer was inspected finding by finding. It still missed unsupported
expectations, promoted methodology suggestions to mandatory requirements and
confused declared environment needs with missing design facts. These observations
are not calibrated reviewer-control false-alarm rates; the scorer leaves those
rates unknown without exact plan-bound controls.

The alternative completed with needs_review. Its source, analysis, plan, review,
knowledge access records, costs and provisional judgments are retained under the
ignored directory artifacts/evaluations/model-quality-2026-10-28/. Human answers
and annotations were never agent inputs. Earlier failures remain in the aggregate
task ledger; the charges above are for the completed workflows only.

One reused baseline and one candidate cannot measure variance, generalization,
KB benefit or the best available model. The source packet and earlier outputs
were already inspected development material. GPT-5 mini was selected as a
budget-feasible EU reasoning-model screen, not a flagship baseline. The application
default model and local environment configuration were not changed.

## Focused instruction experiment

Commit a6c9755 introduced a bundled prompt-version-8 trial: explicit source
coverage checks, source-supported observable expectations, and review findings
grounded in actual source and plan evidence. The schema and orchestration stayed
unchanged. Offline validation passed: 244 tests, Ruff check/format, strict mypy,
and source/wheel build. These checks do not measure semantic quality.

The trial uses the same model/provider, packet, knowledge snapshot and frozen
13-label inventory as the alternative above. It has a $0.30 allocation inside
the original $1 aggregate ceiling and no automatic retry. Its early analysis
introduced a new false source contradiction, so it already fails the declared
no-new-critical-error gate. The planner also transformed an initialization
precondition into required hardware enforcement. The global reviewer then returned
an invalid structured artifact: execution stopped after 19 calls, costing
$0.101128324 with no unsettled charge. No retry was made.

The trial is **rejected** and the application instructions are restored exactly
to prompt version 7. Commit a6c9755 and ignored artifacts under
artifacts/evaluations/prompt-quality-2026-10-28/ preserve the experiment. The failed
run remains in scoring with all 13 obligations; full semantic scoring was not
completed after rejection and those judgments remain unresolved. No separate-case
paid validation was performed because the candidate failed the known-case gate.

Across the original task, confirmed charges are $0.2526491055. The earlier
HTTP-400 reservation remains separately uncertain at $0.308158400. Combined
commitment is $0.5608075055; $0.4391924945 remains under the original $1 ceiling.
Do not count that reservation as confirmed spending or silently release it.

## Next decision

Do not add more prompt instructions or promote a model on these scores alone.
The next implementation candidate should make source obligations and finding
evidence independently inspectable, using SV-05/SV-07 contracts and the existing
SV-06 checks. Exact source references can reject fabricated citations but cannot
prove semantic entailment. Retain engineering adjudication and the regression
cases. Execute separate-case validation only after a candidate clears the known
regressions; a rejected candidate does not justify more paid comparisons.
