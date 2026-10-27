# Planning knowledge checklist

All entries are **proposed and unreviewed**. Original evidence and our proposed adaptations are identified separately. Use the [review template](REVIEW_TEMPLATE.md) to keep, correct or remove entries and state applicability.

These questions are proposed planning guidance. The [source-backed patterns](patterns.md) explain their foundation; individual questions also require engineering judgment. The [OpenHW planning guide](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/VerificationPlanning101.md) supplies the requirement, checking and coverage structure. It does not independently validate every proposed rule below.

## C01 — Source support

Can each claimed hardware behavior be traced to the current specification? Identify assumptions separately; do not invent addresses, timings or reset values.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C02 — Enough context

Are table headings, definitions, related sections and required diagrams present? Record missing material and the specification revision that should govern.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C03 — Normal operation

Does each proposed test state its starting conditions, action and expected result? Can the engineer distinguish a relevant failure from correct behavior?

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C04 — Reset and retained state

Where applicable, cover reset during activity, reset ownership, retained state and explicitly permitted exceptions. Use documented timing and observation points.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C05 — Boundaries and encodings

Where applicable, test immediately below, at and above a threshold, along with supported configuration values. Do not assume behavior for reserved encodings.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C06 — Errors and undefined behavior

Cover documented error responses. Explicitly identify undefined or unspecified behavior without inventing an expected result.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C07 — Interrupts

Where applicable, distinguish event and level interrupts; check trigger conditions, enable/mask behavior and clearing using the actual specification.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C08 — Ordering and interactions

Where applicable, consider simultaneous events, delayed completion and ownership changes between components. Check prerequisites before accepting a handoff.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C09 — Observation and feasibility

State what signal, register or outcome demonstrates pass/fail. Identify missing testbench access, register definitions and timing bounds before calling a test implementable.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C10 — Conflicting requirements

Preserve both conflicting statements and their locations. Request a decision from the design owner instead of choosing a convenient interpretation.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C11 — Missing and duplicate tests

Identify missing requirements and redundant tests. A longer plan is useful only when it adds meaningful checks.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.

## C12 — Scope and limitations

State the features and configurations actually reviewed. Separate incomplete source coverage, unresolved questions and unexecuted test ideas from accepted behavior.

**Use when:** Use for the relevant feature or test type; omit only with an engineering reason.

**Limit:** Proposed adaptation. Source-specific values, assumptions and testbench capabilities must be checked for the target design.
