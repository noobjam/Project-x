# Source auditor evaluation protocol

SV-05 V3 and the early SV-07 audit are implemented for one bounded packet.
Software checks establish persistence, reference validation and budget behaviour.
They do not measure the auditor's ability to detect defects. The evaluation runner
now uses the same source-audit executor as the planning workflow. Authorization
and allocated limits are recorded separately in [progress](../docs/progress.md).

The completed calibration and analysis-only comparison are recorded in
[the 2026-10-29 results](source-audit-results-2026-10-29.md). Execution succeeded
after the correction; the quality gate for downstream planning remains unmet.

## Frozen controls

Eight synthetic inputs were prepared locally on 2026-10-29: three valid controls
and five deliberately defective candidates. They cover retained/lost qualifiers,
omissions, unsupported results, genuine contradictions, different mechanisms and
undefined behaviour. Expectations remain `agent_proposed`, pending engineer review.
No model was called to generate or judge these controls.

The ignored bundle is at
`artifacts/evaluations/source-audit-controls-2026-10-29-v1/`.
Its manifest SHA-256 is
`8ff807b195c5f8212535496d73066768afb6a565f5ee55c8571a3e684a67e1cb`.
The manifest pins every input and a separate reference file. Give the auditor only
one `inputs/Cxx/` directory and its explicitly frozen KB snapshot. Keep `reference/`
and the manifest outside all model context and retrieval. Synthetic candidate
artifacts are evaluation inputs, not prior completed agent tasks or accepted plans.

## Execution and assessment

1. Review the implementation and freeze code/prompt, model/endpoint, KB, generation
   limits and a concrete allocation within the remaining task ceiling. Use
   `prepare-audits` below to bind the supplied candidates to the existing audit
   task. The planning CLI's `audit` command only inspects saved output.
2. Run the auditor on frozen candidates without re-extracting or repairing them.
   Count every call, failure and reservation. Keep labels unchanged after observing
   outputs. Do not count schema-valid mock responses as detection results.
3. An identified assessor maps findings to seeded defects and valid controls using
   cited evidence. Report detected/missed defects, false alarms on valid controls,
   unsupported findings and unassessed findings separately. Matching a kind or ID
   alone is not correct detection. Inspect KB application claims against both the
   entry and source; access records prove only that text was retrieved.
4. Run the frozen real development packet with `--source-accounting --analysis-only`
   only after its allocation is declared. Preserve the existing 13-label denominator
   and compare extracted facts with the retained baseline. Grade the audit separately:
   a correct criticism does not repair the underlying extraction.
5. Proceed to full planning and a separate case only after improved extraction
   without new unsupported behaviour. Semantic gates or repair driven by this
   auditor require measured misses/false alarms and an explicit decision. The
   current audit remains advisory. Engineering acceptance still requires the actual
   Management CPU DOCX and reviewed references.

The controls are small development probes, not a held-out benchmark or proof of
generalisation. The combined V3 path changes extraction mechanics, feedback and
audit behaviour; do not attribute improvement to one component without a separate
comparison. Full-plan adequacy and KB benefit remain separate SV-06/SV-10 questions.

## Source-first corrective condition

Prompt 13 adds one independent reviewer invocation per audit. It receives source
and optional KB only, inventories every passage, then a separate comparison sees
the candidate and that exact inventory. Both stages share the case/run allowance.
The saved source-audit-v1 projection validates both receipts and their bindings;
historical audits remain readable. The inventory is fallible model output, not an
authored reference. No answers or candidate dispositions reach its first pass.

Freeze this as a new condition before paid execution. Preserve all eight controls,
the real packet's thirteen labels and the previous output. Assess whole omissions,
lost qualifiers, unsupported correction advice and valid-control false alarms.
Grade the inventory against source as well as the final findings. A better audit
does not repair the analyst's output or satisfy the gate for full planning.
Offline checks establish isolation, complete passage accounting and recovery only.
The [2026-10-30 results](source-first-results-2026-10-30.md) record the completed
source-first calibration, interrupted real condition and proposed recovery.

## Runner and recovery

Preparation is offline and requires the expected pack manifest hash, a frozen KB
snapshot and explicit model/provider and total cost/call limits. It validates every
candidate before creating an ignored output directory. Only the four allowlisted
input files per case and the KB are copied; reference files are never opened by
the runner. Original bytes and accounting metadata remain intact. Case-prefixed
copies allow all tasks to use one ledger; task bindings locate each exact input.

```sh
uv run --locked python -m soc_verifier.evaluation prepare-audits \
  --bundle artifacts/evaluations/source-audit-controls-2026-10-29-v1 \
  --manifest-sha256 8ff807b195c5f8212535496d73066768afb6a565f5ee55c8571a3e684a67e1cb \
  --knowledge-snapshot artifacts/frozen-knowledge.json \
  --output artifacts/evaluations/auditor-condition/run \
  --model openai/gpt-5-mini --provider azure/swedencentral \
  --max-cost-usd 0.20 --max-model-calls 48 \
  --max-output-tokens 4000 --agent-max-turns 6
```

The KB argument must point to the exact snapshot declared for the condition; the
path above is an example. Preparation saves `source-audit-evaluation-v1`, a hash
binding, effective settings, code/dependency versions and all source references.
Output directories cannot be overwritten. The next command incurs model charges:

```sh
uv run --locked python -m soc_verifier.evaluation run-audits \
  artifacts/evaluations/auditor-condition/run
```

All cases share the configured budget. No analysis or planning is regenerated.
Source-first conditions allow one inventory invocation and one comparison
invocation per case, each with the declared turn limit; the historical path used
one comparison invocation. The first
failure, interruption or exhausted budget ends execution; remaining cases are
reported `not_run`, retaining the full denominator. Completed tasks can be recovered
without inference. Failed or interrupted cases never retry implicitly, including
after restarting the command. A process killed after sending a request can leave
an unknown charge reserved; restarting cannot release it or repeat that case.

`source-audit-case-result-v1` binds each terminal outcome to its task and any
completed audit. `source-audit-evaluation-result-v1` records all cases and spending
at completion; it does not assign semantic scores. For current task spending and
unsettled reservations, this command is local and requires no key:

```sh
uv run --locked python -m soc_verifier.evaluation audit-status \
  artifacts/evaluations/auditor-condition/run
```

## Initial calibration failure and corrective condition

The first condition at a9c482f stopped on its first valid control after three
calls costing $0.00940995, with no uncertain charge. The model returned block IDs
where passage IDs were required, so no audit was accepted. Raw diagnostics also
treated optional specification elaboration suggested by KB checklists as missing
extracted requirements. These are diagnostics, not an accepted eight-case score:
one case failed and seven remain unrun in that condition.

The corrective condition keeps the same eight candidates, reference inventory,
model/endpoint, KB and generation limits. It constrains every selected audit
passage/requirement reference in the output schema and changes the audit instructions
to compare the candidate with the supplied source, distinguishing missing extracted
facts from optional detail absent in both. Prompt version 12 records this behavior;
the persisted source-audit-v1 fields and historical readers remain unchanged.

The first failure remains charged. The corrected condition has a maximum of
$0.19 and 45 model calls; combined with the first trial, these remain below the
original $0.20 / 48-call calibration allocation. It is a separately frozen
condition, not a retry or manual alteration of rejected output. Stop on a further
execution failure. No finding may drive automatic semantic repair, and all
assessment judgments remain provisional. One inspected development control informed
this correction; the set cannot be described as a blind benchmark.
