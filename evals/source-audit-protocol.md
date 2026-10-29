# Source auditor evaluation protocol

SV-05 V3 and the early SV-07 audit are implemented for one bounded packet.
Software checks establish persistence, reference validation and budget behaviour.
They do not measure the auditor's ability to detect defects. This protocol declares
the next evaluation sequence; it does not allocate paid execution.

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
   limits and a concrete allocation within the remaining task ceiling. Build the
   small evaluation runner that binds each supplied candidate to the existing
   source-audit task; the `audit` CLI currently inspects saved output only.
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
