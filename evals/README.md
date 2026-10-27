# Offline evaluation preparation

SV-01A freezes inputs and provenance; SV-03A defines the
[evidence/task conventions](../docs/evaluation-contracts.md). SV-01B/C adds bounded
source packets, versioned annotations and scoring of explicit judgments. Model
comparisons and spending attribution are later work; these commands do not call models.

## Freeze a baseline

Use the locked project environment from a clean repository checkout. Commit the
tooling before freezing, so the recorded commit is reproducible. Inputs and output
must remain local; the command refuses output outside an ignored repository path.
The API key is not required and is never serialized.

```sh
uv run --locked python -m soc_verifier.evaluation freeze \
  --source Management_CPU_ss_spec.docx \
  --reference management_cpu_vplan.xlsx \
  --historical-run artifacts/runs/39b3204e-9398-413a-97b8-aa80908f4e40 \
  --output artifacts/evaluations/management-cpu-baseline

uv run --locked python -m soc_verifier.evaluation verify \
  artifacts/evaluations/management-cpu-baseline --check-originals
```

The historical run argument is optional. It must name a run of the same source
document. Its canonical artifacts are frozen as historical reference material;
they are not a controlled baseline for the migrated runtime.

The bundle separates:

| Location | Use |
| --- | --- |
| source/ | Exact DOCX bytes and fresh Specification JSON from the actual DOCX adapter. |
| reference/ | Human-authored workbook, explicitly imported and unreviewed for evaluation. |
| historical/ | Prior source, run manifest, result, analysis, plan and review; never runtime evidence. |
| provenance/ | Dependency lockfile. The manifest also pins Git commit/tree, installed versions, prompt version, domain schema hashes and allowlisted settings. |
| manifest.json and manifest.sha256 | Inventory and integrity checksum; the JSON manifest is written last. |

Only source/specification.json is the declared runtime input. Never pass the
whole bundle, manifest, human plan or historical output as agent context. No
generic directory retrieval is enabled by this tooling.

Existing bundles are never overwritten. A failed freeze may leave an incomplete
directory without a completion manifest; use a new output path after addressing
the error. Verification detects changed or missing frozen files, unsupported
manifest formats and path escapes. --check-originals additionally detects drift
at the original local paths. Without it, a frozen bundle remains verifiable after
the original files move or change. Checksums detect accidental drift; they are not
signatures or proof of semantic correctness.

## Initial case scope

| Case | Role | State after this milestone |
| --- | --- | --- |
| Management CPU full DOCX | Primary end-to-end acceptance workload | Source/reference frozen locally; no model execution or engineering acceptance. |
| Private table, reset and contradiction packets | Development diagnostics | Three local projections from fresh ingestion of the frozen DOCX, with headers and related definitions. Source context and labels await engineering review. |
| OpenTitan UART | Public portability diagnostic | RX FIFO reset, watermark and overflow; pinned source recipe in [opentitan.json](opentitan.json). |
| OpenTitan USB suspend/resume | Integration diagnostic | USBDEV, AON wake, Earlgrey pinmux retention and power-manager wake recording. Includes the relevant CSR definitions and contributing text sources. |

Keep source scopes and reference inventories versioned. Previously inspected
private references are development/regression material, not blind gold. Public
examples may be familiar to models. Annotations distinguish proposed, imported,
reviewed and disputed labels and keep missing evidence visible. The prepared real
pilot has no human-reviewed labels or engineering-acceptance result.

## Prepare and verify source packets

[The public recipe](opentitan.json) pins OpenTitan revision
`d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06`, individual file hashes and inclusive
line ranges. It retains the Apache-2.0 license. The selection follows the
[USB handoff procedure](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/doc/wake_resume.md),
[Earlgrey pinmux description](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/pinmux/doc/theory_of_operation.md)
and [power-manager description](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/pwrmgr/doc/theory_of_operation.md).
No authored testplans, tests or coverage implementations are downloaded.

Only fetch-public uses the network, to download those pinned public source files.
Preparation, verification, scoring and normal tests are offline.

```sh
uv run --locked python -m soc_verifier.evaluation fetch-public \
  --recipe evals/opentitan.json --output artifacts/evaluations/opentitan-source
uv run --locked python -m soc_verifier.evaluation prepare-public \
  --recipe evals/opentitan.json --source-root artifacts/evaluations/opentitan-source \
  --output artifacts/evaluations/new-pilot
uv run --locked python -m soc_verifier.evaluation prepare-private \
  --baseline artifacts/evaluations/management-cpu-baseline \
  --selection artifacts/evaluations/pilot-2026-10-27/private-selection.json \
  --output artifacts/evaluations/new-pilot
```

The private selection stays local. It binds the baseline manifest hash and lists
each case's ID, scope, exact source block IDs and limitations. Preparation reruns
the actual DOCX adapter, rejects any change against the frozen extraction, and
preserves selected text, IDs, row headers and locators without rewriting them.

The public adapter is deliberately a line projection of selected Markdown/HJSON
source, not a rendered-document or HJSON parser. It retains each nonempty line's
text and original line locator. Block IDs include the complete original-file hash,
so identical line numbers in different documents cannot collide. The projected
Specification uses a source-package digest; original file hashes remain separate
in packet.json. Figures and omitted material remain limitations.

Every packet contains source/specification.json, packet.json and packet.sha256.
Only the explicit Specification file is agent input. Put annotations, assessments
and result artifacts under reference/, outside retrieval. Do not give an agent
the entire evaluation directory. Source projection directories cannot be overwritten.

## Annotations and assessments

The persisted evaluation formats are defined in
[scoring.py](../src/soc_verifier/evaluation/scoring.py); they are independent of
the application's existing domain schemas and prompt version.

An annotation file binds the case ID and exact source JSON hash, declares its
revision and whether coverage is unknown, and holds a fixed label inventory:

- Obligations describe expected behavior or correct identification of a source
  conflict. Source spans bind document/block identity, text hash and Unicode
  code-point offsets. A valid span is not proof of semantic support.
- States are agent_proposed, imported_reference, human_reviewed or disputed.
  Imported references need their origin and file hash; reviewed labels require an
  identified reviewer. Preserve reference provenance when review state changes.
- Unavailable evidence requires a reason and remains in the obligation denominator.
  Uninterpreted visual content is coverage unknown; do not invent obligations to
  fill it. Exclusions are limited to reviewed non-normative/out-of-scope decisions
  with a reason and authority. Parsing failures cannot be exclusions.
- Reviewer controls describe valid or defective plan items and bind the exact
  candidate plan hash and item ID. Changing a seeded candidate requires new controls.

An assessment is separate from annotations and agent output. It pins the source,
annotation file and each supplied analysis/plan/review artifact. An identified
assessor supplies obligation-to-output judgments, scenario adequacy, support
judgments for output items and reviewer-control judgments with finding indices.
The scorer validates references and aggregates those judgments; it does not make
semantic matches, call an LLM judge or infer correctness from linked IDs.

Increment label revisions for changed expectations. A changed source packet needs
new source-bound annotations, even when logical label IDs stay the same. Freeze
scope before seeing candidate output; never shrink the inventory to fit a candidate.

```sh
uv run --locked python -m soc_verifier.evaluation verify-packet \
  artifacts/evaluations/pilot-2026-10-27/management-reset \
  --annotations artifacts/evaluations/pilot-2026-10-27/management-reset/reference/annotations.v001.json
uv run --locked python -m soc_verifier.evaluation freeze-pilot \
  artifacts/evaluations/new-pilot
uv run --locked python -m soc_verifier.evaluation verify-pilot \
  artifacts/evaluations/pilot-2026-10-27
```

Before freeze-pilot, place each packet's reviewed-or-provisional annotations at
reference/annotations.v001.json (or supply --annotations-file with another explicit
reference path) and commit preparation code. The inventory pins the code commit,
packet/source/annotation bytes and any local selection recipes. Existing inventories
are not overwritten. Use a new pilot directory for a later version. The existing
local pilot already has its sources and annotations; use verify commands on it.

## Score supplied outputs without inference

With independently prepared assessments and explicit saved outputs:

```sh
uv run --locked python -m soc_verifier.evaluation score \
  --packet artifacts/evaluations/pilot-2026-10-27/management-reset \
  --annotations artifacts/evaluations/pilot-2026-10-27/management-reset/reference/annotations.v001.json \
  --assessment artifacts/evaluations/assessment.json \
  --analysis artifacts/evaluations/analysis.json \
  --plan artifacts/evaluations/plan.json --review artifacts/evaluations/review.json \
  --output artifacts/evaluations/score.json
```

Report dimensions are separate: obligation recall, scenario adequacy, supported/
unsupported/unresolved output items, reviewer defect detection and false alarms.
Reviewed, provisional and disputed labels have separate groups. A zero denominator
produces an unknown rate, not a perfect score. Reviewer false-alarm rates use
assessed valid controls and expose unassessed controls; unmapped findings remain
unassessed. Item-support counts are not counts of atomic claims.

Missing judgments remain unresolved. Failed, malformed, interrupted and budget-
exhausted runs retain the fixed denominator and completion status. Invalid output
schemas/links are reported as malformed, with the declared status also preserved.
Stale hashes or fabricated assessment references fail explicitly.

A packet-level semantic pass requires reviewed context, labels and judgments,
available evidence, known coverage, complete valid outputs, no unresolved judgments
or unmapped findings, full declared obligation/scenario coverage and no unsupported
items or failed controls. This is never full-document acceptance. Editing time is
explicitly not measured. The real pilot's labels and context are provisional;
synthetic test passes only validate scoring behavior.

Run the deterministic controls with `uv run --locked pytest tests/evaluation`.
They cover output deletion, source mutation with new labels and unchanged controls,
stale artifacts, evidence availability, unsupported output, weak scenarios, reviewer
false alarms and incomplete runs. No model output or engineering quality is measured
by those software tests.

Progress, remaining acceptance criteria and the paid-run proposal are tracked in
[project progress](../docs/progress.md) and [the roadmap](../docs/agent-roadmap.md).
