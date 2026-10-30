# Agent quality comparison

This SV-10 development experiment distinguishes model limitations from workflow
limitations before expanding agent schemas. It is not engineering acceptance.

## Frozen conditions

Use the same source packet, full knowledge snapshot, specialist instructions,
tools, output contracts, revision limit and call/turn limits. Compare the existing
Gemini 3.1 Flash Lite / Google EU condition with GPT-5 mini / Azure Sweden Central.
This changes the model/provider bundle, not just the model. GPT-5 mini is a
budget-feasible reasoning-model screen, not a flagship or SOTA baseline. Preserve
provider defaults for unspecified generation/reasoning parameters and record them
as a comparison limitation. Do not change the application's default model.

The alternative endpoint must advertise tools and structured output. Pin routing,
disable fallback, deny data collection and require zero data retention. Existing
cost reservations and the original aggregate task cap remain enforced. Stop on a
failure; do not automatically retry or change models. A later condition requires
a recorded allocation that fits the remaining balance, including unknown charges.

Freeze source/knowledge/configuration/runtime hashes, label revisions, run
allocations and the runner before inference. Record prior failures. A historical
baseline can be reused only after matching all effective inputs other than the
declared model/provider condition and its accounting allocation.

## Quality criteria

Use the existing source-bound annotations and explicit-judgment scorer described
in [the evaluation guide](README.md). Preserve original annotations and increment
the revision when adding omitted obligations. Freeze the revised inventory before
new output. Previously inspected cases remain development diagnostics.

Assess each obligation against extracted requirements and plan items:

- **Extraction:** the condition, required behavior, units and exceptions survive.
  Partial extraction does not count as complete coverage.
- **Scenario:** setup and stimulus reach the relevant condition; an observation
  and expected result distinguish compliant behavior from a relevant violation.
  Unknown environment access remains an explicit need. Generic claims that the
  system works do not count as adequate checks.
- **Support:** distinguish supported, unsupported and unresolved output items.
  Undefined source behavior cannot become a required response. An observation
  method may be an environment need, but cannot invent hardware behavior.
- **Review:** inspect every finding against its cited source and actual output.
  Record useful defects, false alarms and unresolved judgments separately.
  The existing scorer's reviewer-control rates require exact plan-bound controls;
  narrative review judgments must not be misrepresented as those rates.

Semantic assessments are agent_proposed until the engineer reviews them. Tool
receipts, row counts, structurally valid output and offline software tests do not
establish quality. A connected-only model comparison cannot establish KB benefit.

## Decision and follow-up

Report completion, obligation recall, scenario adequacy, unsupported/unresolved
items, review findings, confirmed charges and outstanding reservations separately.
Keep incomplete runs in the record. One execution per condition is exploratory;
it does not measure variance or establish the best model.

If a model change materially improves the targeted failures, validate it on a
separate development packet before changing defaults. If misses remain, trial the
smallest relevant SV-05/06/07 change with the same criteria. Neither an aggregate
score nor extra prose offsets a new critical miss or invented behavior. Keep
source material, labels, generated plans and detailed judgments in ignored local
artifacts. Only the protocol and source-free aggregate status belong in Git.
