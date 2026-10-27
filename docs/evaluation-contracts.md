# Evidence and task conventions

SV-03A design contract. These conventions and synthetic examples guide later
SV-02/03B work; they do not change the current runtime schemas, IDs or resume rules.

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

Later reuse must match the complete fingerprint, including split child inputs.
Matching a filename, batch number or item count is insufficient. The runtime must
receive explicit snapshot references instead of choosing whichever artifact is
latest. The example is a design fixture, not a new checkpoint format.

## Compatibility and review boundaries

The offline evaluation manifest has its own format identifier. It is never passed
to an agent or used as an application run manifest. Existing domain schemas remain
1.0 and PROMPT_VERSION remains unchanged in this milestone.

SV-01B/C implements these coordinates in evaluation-only packets and annotations,
with explicit packet/label/output hashes for scoring. This does not introduce the
SV-02 task envelope or change application checkpoint reuse. Public projections retain
original-file document hashes separately from their package and projected JSON hashes.

When later changes require new domain schemas, retain explicit V1 readers and
dispatch by artifact type/version. Adapt only in memory for export, reject unknown
versions and incompatible resume combinations, and keep spend ledger readers
independent. That implementation belongs to SV-03B, not this design slice.

The first future repair can replace selected existing plan items only, retaining
IDs and requirement references against a frozen source, analysis and partition.
It must check base-plan/target-item hashes, write a new revision and preserve
unaffected serialized items. Analysis mutation needs a separate lineage design.
