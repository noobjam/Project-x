# Knowledge curation review

Help us curate reusable knowledge for an agent that reads chip specifications and drafts verification plans.

**Status: 36 proposed entries, zero engineering-approved entries.** These documents are review material; they are not connected to runtime retrieval. Approval concerns the suitability of selected knowledge entries, not agent quality or testbench readiness.

## Start reviewing

1. Read [sources and comparable systems](sources.md) for provenance and what similar agents actually use.
2. Review [source-backed patterns](patterns.md), starting with K01–K04 for planning and K05–K09 for testbench/interface guidance.
3. Review the [planning checklist](planning-checklist.md), [testbench subchecklists](testbench-checklists.md) and [worked examples](examples.md).
4. Comment on the review pull request using the [review template](REVIEW_TEMPLATE.md). Use **Keep**, **Correct**, **Remove** or **Need more information**, with entry IDs and applicability. Partial reviews are useful.

Everything can be read directly on GitHub. To leave a line-specific comment, open the pull request's **Files changed** tab and select the relevant line. To propose an edit, use a review suggestion or a follow-up pull request. Keep comments limited to this public material.

## Contents

| Material | IDs | Count | What to assess |
| --- | --- | --- | --- |
| [Source-backed patterns](patterns.md) | K01–K12 | 12 | Source interpretation, reusable rule, applicability and limits |
| [Planning checklist](planning-checklist.md) | C01–C12 | 12 | Useful questions, exceptions and omissions |
| [Testbench subchecklists](testbench-checklists.md) | TB01–TB07 | 7 groups / 21 subchecks | Separate environment capabilities a plan should consider |
| [Worked public examples](examples.md) | E01–E03, E08–E09 | 5 | Setup, action, observation and meaningful pass/fail behavior |

The source mix spans **OpenHW, Accellera, PULP and OpenTitan**, with an authoritative RISC-V cross-check. [Sources](sources.md) also documents data usage reported by Spec2Plan, Intel's formal testplanning work, HAVEN, ChipNeMo and STELLAR.

Original passages are distinguished from our proposed adaptations. **K04 and K12 need particular attention:** they expose source disagreements that should not be silently imported into the knowledge base.

This public edition preserves entry IDs from the local 40-entry handoff. Four private project examples and the private supporting documents remain local, which accounts for the gaps in example numbering.

## What your greenlight means

For each selected entry, confirm the corrected wording, source interpretation, applicability and unresolved limitations. Record your name or reviewer ID and the revision reviewed. Blank or untouched entries remain unreviewed; a GitHub merge alone does not confer engineering approval.

We will reconcile the decisions into versioned knowledge entries. Before runtime integration, select separate evaluation cases and keep their engineer-written answers hidden from the agent. Examples supplied as knowledge cannot also serve as independent tests of the knowledge's benefit. Public material may already be familiar to the model.

The next implementation ticket and execution boundaries remain in [project progress](../progress.md) and the [roadmap](../agent-roadmap.md). This review does not implement retrieval, change agent behavior or run paid evaluations.
