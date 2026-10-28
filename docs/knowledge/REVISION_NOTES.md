# Revision 2: engineering feedback and follow-up review

Prepared 28 October 2026 on draft PR #4. **Status: proposed revisions, engineering confirmation pending.** All four comments were received from GitHub reviewer `5a1aah` on 27 October. They identify additions/corrections; they do not approve the entire pack. No runtime change or test execution is claimed.

## Changes mapped to comments

| Feedback | Revision | Confirmation needed |
| --- | --- | --- |
| [Add clock/reset, data/control and register rules](https://github.com/noobjam/Project-x/pull/4#issuecomment-6454839896) | [K13–K15](patterns.md#k13--plan-clock-and-reset-connectivity-checks-from-the-specification), with required inputs, methods, evidence and limitations | Does the condensed wording retain the essential checks? Which methods/dependencies are required versus optional? |
| [Finish the plan and record missing information](https://github.com/noobjam/Project-x/pull/4#issuecomment-6454918911) | [C10](planning-checklist.md#c10--conflicting-requirements) preserves both sources, links the open question to affected rows, leaves unsupported expectations unresolved and continues the draft | Is this enough information for the design owner to resolve the gap afterward? |
| [Do not require covergroups for every test](https://github.com/noobjam/Project-x/pull/4#issuecomment-6455313481) | [TB06](testbench-checklists.md#tb06--coverage-and-traceability) and [K03](patterns.md#k03--separate-stimulus-choices-from-coverage-evidence) accept meaningful test/assertion results and select extra coverage only when useful | Which cases can use pass/fail evidence, and where is additional scenario/configuration evidence necessary? |
| [Examples are too few and project-specific](https://github.com/noobjam/Project-x/pull/4#issuecomment-6455401309) | [E10–E18](examples.md#e10--check-address-boundaries-and-overlapping-decode-rules), a behavior index, and transfer limits for the original five cases | Are these behavior families relevant to your work? Identify a missing family or a case that would not transfer as written. |

## Read these first

1. **K13–K15:** the three new rules, adapted from the engineer's proposals. Their planning steps do not imply the agent can run formal tools or UVM tests. Numerical timing and code templates are not assumed.
2. **E10–E12 (PULP crossbar):** address boundaries/overlap, error versus default routing, and ordering with outstanding requests. The address table in E10 is explicitly a synthetic test configuration.
3. **E13–E14 (PULP mailbox):** masking versus sticky status, write-one acknowledgement, destructive reads and access errors. **E14 exposes conflicting reset values in the source**; confirm the governing value or retain it as unresolved.
4. **E15/E17 (CV32E40P) and E16/E18 (CORE-V MCU):** boot permission after reset, acknowledgement validity, two-level event mapping and clock-domain assignments. They are independently pinned examples; no assumption is made that the MCU uses the separately pinned core revision.
5. **C10 and TB06:** automation should finish the draft, while evidence and unresolved questions remain specific to the affected checks.

Use [the review template](REVIEW_TEMPLATE.md) with exact entry IDs and the commit reviewed. Confirm suitability, corrections, applicability and open questions. Untouched entries remain unreviewed. Approving a knowledge entry does not establish that the generated agent plans are adequate.

## Deliberate qualifications to the proposed rules

- Formal results are conditional on the model and assumptions; no universal proof completeness or runtime claim is retained. Reachability and inconclusive results stay visible.
- Reset release is specified by the actual timing contract, not inferred solely from synchronizer depth. Clock quality and CDC/RDC safety need separate checks.
- Registers excluded from generic testing need targeted checks or explicit gaps. A generated register model is not an independent oracle merely because it matches generated RTL.
- Tests and formal assertions need appropriate evidence under TB06. Passing one checked case does not establish every configuration of the feature.
- The original assertion snippets remain in the linked comment as illustrative proposals. No executable template has been copied or claimed validated.

## Runtime follow-up after curation

The current export already has an **Open questions** column. Source gaps also avoid revision retries. This revision defines the desired handling more clearly; reliable links from gaps to affected requirements/plan rows remain work for the planned findings/review slice (SV-07/SV-09). SV-04 remains the next implementation ticket for source retrieval.

Before any approved examples guide the agent, select separate evaluation cases and compare with/without knowledge on missed checks, unsupported facts, unresolved questions and cost. Keep reference answers hidden. No source above establishes generalization to a new design, and no paid evaluation or runtime integration is part of this documentation revision.
