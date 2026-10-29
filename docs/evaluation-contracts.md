# Evidence and task conventions

SV-03A conventions, implemented for runtime tasks by SV-02/minimal SV-03B.
Evaluation annotations and application artifacts retain separate contracts.

## Source identity and coordinates

- Keep the original DOCX SHA-256 over its exact bytes. The frozen specification
  JSON has its own file hash; never substitute that hash for the document hash.
  For this DOCX adapter, the document ID is the original DOCX SHA-256. Public
  projections will need an explicit mapping to their original source/package.
- Existing P/T block IDs are stable within a pinned document and ingestion version.
  A multi-document reference is the pair of document ID and block ID. Do not claim
  identity persists after document editing or normalize all existing IDs now.
- Spans address the exact persisted SourceBlock.text: zero-based Unicode code
  points, half-open [start, end). Hash the complete text as UTF-8, without trimming,
  casefolding or newline conversion. Retrieve text[start:end] only after confirming
  the document/block identity and text hash, with 0 <= start < end <= len(text).
- A casefolded search string can have a different length. Its offsets cannot be
  used directly in the original text. Tabs, CR/LF, repeated phrases and emoji must
  retain their coordinates. Pin the adapter/normalization version before annotations.
  The baseline Git commit pins the current adapter; future projections must record
  their own processing version alongside the source identity.
- A valid reference establishes location and integrity, not entailment. Missing
  spans in historical artifacts stay unavailable; never reconstruct confidence.

The synthetic fixture in tests/fixtures/evaluation/contract-examples.json includes
two occurrences of RESET, an expanding casefold character, a tab, CR/LF and an
emoji. Its source file and declared spans are checked offline.

## Task identity and reuse

A logical task has an opaque ID. Execution attempts are separate. Its input
fingerprint covers:

- Role, stage and assigned IDs, preserving meaningful list order.
- Exact input artifact paths within the snapshot and their byte hashes, including
  source, analysis, plan and review revisions when applicable.
- Effective prompt/schema/tool versions, engine/code revision and all effective
  model/provider/generation limits that can change behavior.

Encode the fingerprint payload as JSON with sorted keys, UTF-8, no ASCII escaping,
no insignificant whitespace and no NaN/Infinity; hash those bytes with SHA-256.
Task IDs, timestamps, secrets, machine paths and attempt counters are not themselves
part of the behavior fingerprint. They must not replace its input content.

Reuse matches the complete fingerprint, including split child inputs. Matching a
filename, batch number or item count is insufficient. Task tools receive explicit
snapshot references. The synthetic example remains a convention fixture, not a
production checkpoint.

## Runtime records and compatibility

- `execution.json` (`task-execution-v1`) pins source bytes, original document hash,
  installed source/dependency versions, prompt/tool/source-processing versions and
  behavior configuration. Source code is hashed independently of documentation-only
  Git commits. Worker scheduling is excluded; output ceilings are included.
- `*.task.json` (`agent-task-v1`) stores the opaque task ID, ordered assignments,
  input/schema/instruction hashes, exact evidence references and parent fingerprint.
- `*.completed.json` (`task-completion-v1`) atomically stores the result plus its
  input binding and output hash. Canonical output JSON is a recoverable projection.
- `*.split.json` (`task-split-v1`) binds each partition to its task and input hash.
- Invocation/call records distinguish logical work, correction/restart invocations,
  individual model turns and failures. Reservations add task/invocation/call IDs;
  legacy reservation/settlement amounts remain readable without inference.

Run manifests/results use version 2.0 and engine `openai-agents-v2`; domain source,
analysis, plan and review schemas remain 1.0. Prompt version 11 adds the opt-in
passage accounting/feedback and source-audit behavior; separate draft/report
formats use version 3.
The report binds exact source, extraction and projected analysis artifact hashes.
Source-passage IDs are computed from exact persisted text and constrained by the
output schema for both obligations and dispositions; Python supplies their Unicode
spans/quotations. Earlier V1 quote-based and V2 block-disposition drafts/reports
remain readable. V1 validates exact occurrence matches.
Missing references and normalized/paraphrased V1 quotations fail. Unselected text without
a disposition stays unaccounted. Location validity and model-proposed dispositions
never establish semantic coverage or engineering approval. Unknown
versions and stale fingerprints fail explicitly. Legacy runs can export and report
spending with task metadata unavailable, but cannot resume under the new engine.
No immutable legacy artifacts are migrated or rewritten.

V3 extraction saves unaccepted `attempt0`/`attempt1` task completions separately
from the accepted canonical extraction. `source-accounting-feedback-v1` binds
the rejected draft and precise issues. Only disposition conflicts/duplicates
permit one correction; obligations and gaps are frozen. Replaying saved attempts
cannot renew this allowance. Unknown references and exhausted attempts fail.

`source-audit-v1` is a separate reviewer task bound to source, analysis, accounting
and optional KB snapshots. Findings cite exact passage/requirement IDs. Conflict
comparisons require two distinct cited source passages. Knowledge application
claims require entries actually read by this task. Its completion preserves the
same immutable receipt rules; CLI/export revalidate source and access bindings.
The judgments remain `agent_proposed` and advisory. Empty findings, valid references
and recorded reads do not constitute semantic acceptance. The frozen control pack
and [evaluation protocol](../evals/source-audit-protocol.md) keep calibration labels
outside agent input. `--analysis-only` stops after this audit; it does not alter
task fingerprints or grant additional execution budget.

The source-processing label `docx-v1` identifies the existing DOCX representation;
its exact input bytes and runtime source hash are also pinned. This does not claim
new offsets, visual interpretation or stable block IDs across edited documents.
Evaluation-only source spans continue to validate exact Unicode text and hashes.

The reasoning replay adapter is a separately recorded behavior condition
(`openrouter-v1`). It preserves provider metadata across tool calls. Instrumentation
leaves ordinary message content/settings unchanged; offline checks cannot prove
engineering quality or compatibility with every live provider.

The first future repair can replace selected existing plan items only, retaining
IDs and requirement references against a frozen source, analysis and partition.
It must check base-plan/target-item hashes, write a new revision and preserve
unaffected serialized items. Analysis mutation needs a separate lineage design.
