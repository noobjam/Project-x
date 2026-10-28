# Knowledge curation review

Help us curate reusable knowledge for an agent that reads chip specifications and drafts verification plans.

**Status: revision 2, 48 proposed entries, zero engineering-approved entries.** Four engineering comments have been incorporated into proposed revisions; the edited entries need confirmation. These documents are review material; they are not connected to runtime retrieval. Approval concerns the suitability of selected knowledge entries, not agent quality or testbench readiness.

## Start reviewing

For the follow-up review, start with [what changed and decisions needed](REVISION_NOTES.md): K13–K15, C10, TB06/K03 and E10–E18. The notes link each change to the original comment. No blanket reapproval of untouched entries is implied.

1. Read [sources and comparable systems](sources.md) for provenance and what similar agents actually use.
2. Review [source-backed patterns](patterns.md), starting with K01–K04 for planning and K05–K09 for testbench/interface guidance.
3. Review the [planning checklist](planning-checklist.md), [testbench subchecklists](testbench-checklists.md) and [worked examples](examples.md).
4. Comment on the review pull request using the [review template](REVIEW_TEMPLATE.md). Use **Keep**, **Correct**, **Remove** or **Need more information**, with entry IDs and applicability. Partial reviews are useful.

Everything can be read directly on GitHub. To leave a line-specific comment, open the pull request's **Files changed** tab and select the relevant line. To propose an edit, use a review suggestion or a follow-up pull request. Keep comments limited to this public material.

## Contents

| Material | IDs | Count | What to assess |
| --- | --- | --- | --- |
| [Source-backed and engineer-contributed patterns](patterns.md) | K01–K15 | 15 | Source interpretation, reusable rule, applicability and limits |
| [Planning checklist](planning-checklist.md) | C01–C12 | 12 | Useful questions, exceptions and omissions |
| [Testbench subchecklists](testbench-checklists.md) | TB01–TB07 | 7 groups / 21 subchecks | Separate environment capabilities a plan should consider |
| [Worked public examples](examples.md) | E01–E03, E08–E18 | 14 | Setup, action, observation, meaningful pass/fail behavior and transfer to another design |

The source mix spans **OpenHW, Accellera, PULP and OpenTitan**, with an authoritative RISC-V cross-check and attributed engineering contributions. Worked examples now span four projects: OpenTitan (5), PULP AXI (5), CV32E40P (2) and CORE-V MCU (2). The behavior index in [examples](examples.md#find-a-behavior-then-check-applicability) explains how to choose a case without assuming that a familiar block name implies matching behavior. [Sources](sources.md) also documents data usage reported by Spec2Plan, Intel's formal testplanning work, HAVEN, ChipNeMo and STELLAR.

Original passages and paraphrased source facts are distinguished from our proposed adaptations. **K04, K12 and E14 need particular attention:** they expose source disagreements that should not be silently imported into the knowledge base. K13–K15 retain the engineer's methodological input without claiming their illustrative assertion code was validated.

This public edition preserves existing entry IDs from the local 40-entry v1 handoff and adds K13–K15 and E10–E18. Four private project examples and the private supporting documents remain local, which accounts for the gaps in example numbering. The ignored HTML/ZIP v1 handoff is an unchanged historical snapshot; use this GitHub edition for revision 2 review.

## What your greenlight means

For each selected entry, confirm the corrected wording, source interpretation, applicability and unresolved limitations. Record your name or reviewer ID and the revision reviewed. Blank or untouched entries remain unreviewed; a GitHub merge alone does not confer engineering approval.

We will reconcile the decisions into versioned knowledge entries. Before runtime integration, select separate evaluation cases and keep their engineer-written answers hidden from the agent. Examples supplied as knowledge cannot also serve as independent tests of the knowledge's benefit. Public material may already be familiar to the model.

The next implementation ticket and execution boundaries remain in [project progress](../progress.md) and the [roadmap](../agent-roadmap.md). This review does not implement retrieval, change agent behavior or run paid evaluations.
