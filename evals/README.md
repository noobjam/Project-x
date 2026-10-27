# Offline evaluation preparation

SV-01A freezes inputs and provenance; SV-03A defines the
[evidence/task conventions](../docs/evaluation-contracts.md). Source packets,
annotation/scoring implementations and model comparisons are later substeps.

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
| Private table, reset and contradiction packets | Development diagnostics | Selection and source-completeness checks belong to SV-01B. |
| OpenTitan UART | Public portability diagnostic | Supporting source acquisition/fixture adapter belongs to SV-01B. Use a pinned revision, not a moving branch. |
| One cross-IP packet | Integration diagnostic | Select contributing sources in SV-01B; USB suspend/wakeup is a candidate only. |

Keep source scopes and reference inventories versioned. Previously inspected
private references are development/regression material, not blind gold. Public
examples may be familiar to models. SV-01C will distinguish proposed, imported,
reviewed and disputed labels and keep missing visual evidence visible. Nothing in
this milestone supplies reviewed labels or a semantic pass.

Progress, remaining acceptance criteria and the paid-run proposal are tracked in
[project progress](../docs/progress.md) and [the roadmap](../docs/agent-roadmap.md).
