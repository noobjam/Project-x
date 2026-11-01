# What to borrow now from Synopsys verification agents

Reviewed 2026-10-29 against local code at e638533. This is a focused design
comparison, not engineering approval, a runtime change or a new research council.
The user subsequently approved the scoped changes on 2026-10-29. Their implementation
and validation status is in [progress](progress.md), with scope in the existing
[roadmap](agent-roadmap.md) tickets. The comparison below records the pre-change gaps.

## Published evidence

GPT-Synopsys is the specialized-model development partnership announced on
September 30. Its planned service includes Synopsys tools and interoperability
with customer agent systems. The announcement does not disclose an extraction
benchmark, prompts or training dataset. [Joint announcement](https://news.synopsys.com/2026-09-30-OpenAI-and-Synopsys-Announce-GPT-Synopsys-Frontier-Intelligence-to-Revolutionize-Chip-Design).

The more actionable architecture is AgentEngineer/Autopilot. Synopsys describes
supervising agents that evaluate intermediate outputs and choose subsequent work,
bounded task agents, and engineering tools that validate results. Shared services
include engineering knowledge, reusable skills, persistent memory and telemetry;
people can inspect and redirect work at checkpoints.
[Architecture description](https://www.synopsys.com/blogs/chip-design/long-horizon-agentengineer-solutions.html).

Its DV demonstration starts with a specification, RTL, existing tests and coverage
targets. It generates plans/testbenches, runs regressions and responds to failures
and coverage gaps. The reported gains concern those demonstrations; they do not
establish reliable plan extraction from an arbitrary specification alone.
[Demonstration account](https://www.synopsys.com/blogs/chip-design/agentic-ai-drives-verification-closure-thermal-analysis.html).

Synopsys also supplies specification-linked plans, UVM environments, tests and
protocol checks through its licensed VIP Test Suites. This is evidence of reusable
verification collateral, not evidence that those suites are GPT-Synopsys training
data or a publicly reusable knowledge dataset.
[Test Suites](https://www.synopsys.com/verification/verification-ip/verification-test-suites.html).

For a concrete comparison outside Synopsys, NVIDIA and Siemens describe a fixed
model/harness experiment using final Liberty-file verification, trajectory
inspection and changes to skills/tool interfaces. They report a development score
increase from about 55% to 95%, with fewer turns. The verifier measures completeness,
validity, numerical accuracy and integrity against references. This is a different
task with executable numerical checks; its scores cannot transfer to our natural
language plans. [Technical account](https://developer.nvidia.com/blog/optimizing-agent-reliability-and-tool-calling-efficiency-for-chip-design-using-nvidia-nemo-gym/).

These are primary vendor/partner accounts, not independent replication. Synopsys
announced end-of-2026 availability for AgentEngineer/Autopilot. Detailed knowledge
schemas, retrieval algorithms, correction limits and specification-understanding
error rates are not established by the sources reviewed.
[Availability and platform announcement](https://news.synopsys.com/2026-09-28-Synopsys-Powers-Autonomous-Engineering-with-a-Broad-Portfolio-of-Long-Horizon-Agents-and-Autopilot-Platform).

## Comparison at e638533

Our evidence is [the implemented architecture](architecture.md),
[retained trial results](../evals/source-accounting-comparison.md),
[workflow](../src/soc_verifier/workflows/spec_to_plan/workflow.py),
[accounting validator](../src/soc_verifier/domain/accounting.py), and
[existing knowledge procedures](knowledge/patterns.md). The following changes
are our engineering proposals, not claims about Synopsys internals.

| Mechanism to examine | What we already have | Specific gap and proposed adaptation |
| --- | --- | --- |
| Evaluate intermediate results and act on failures | Python stage routing, three SDK specialists, limited citation corrections, optional revisions | Accounting failures terminate without corrective feedback. Give the analyst exact validator findings and permit one bounded correction of an unaccepted draft. Keep semantic uncertainty separate. |
| Use engineering knowledge as repeatable procedures | Frozen KB, applicability guidance, checklists, worked examples and K13–K15 procedures | Access logs prove retrieval only. Assess which procedure was applied to which requirement and whether its assumptions hold; start with an existing behavior family. |
| Validate outcomes with independent evidence | Source-ID checks, exact spans, explicit assessments and frozen labels | Correct citations can accompany missing qualifiers or unsupported conclusions. Add a source-based audit before planning and measure its misses and false alarms. |
| Supply task-appropriate design context | Specification, selected KB entries and prior task artifacts | We do not supply RTL, existing regression results or coverage targets. State missing inputs and limit the draft's claims accordingly; current scope remains verification planning. |
| Preserve state and inspect costs | Immutable checkpoints, task/call ledgers, versions and ignored private diagnostics | Keep these foundations. Persist correction attempts and reasons without treating model-generated memory as approved engineering knowledge. |

The latest failure also exposed our own contract mismatch: evidence selects
passages, while dispositions classify entire blocks. A block can contain both an
obligation and an informative cross-reference. Changing only the prompt leaves
that ambiguity in the interface. Align disposition scope with the evidence units
and keep every unexplained passage visible. That still cannot prove semantic
completeness.

## Proposed next slice and acceptance

1. **SV-05: repair the interface and feedback path.** Use synthetic mixed-content
   cases to define passage-scoped dispositions and structured validation errors.
   Trial at most one pre-acceptance mechanical correction, retaining both raw
   attempts, affected IDs, source hashes and all charges. Unknown IDs, repeated
   errors or exhausted budgets still stop. A correction must not silently discard
   valid obligations to make a validator pass. Historical readers remain supported.
2. **SV-07, narrow prerequisite: audit extraction before planning.** Reuse the
   reviewer role to identify missing qualifiers and unsupported claims with exact
   source evidence. A claimed contradiction must identify the subject, conditions
   and incompatible statements; an unknown relationship stays unresolved. Evaluate
   against both defective and valid controls before using findings to block or
   repair work. An LLM audit is fallible evidence for review, not a proof engine.
3. **SV-06/SV-10: measure use of existing knowledge.** Inspect application of a
   small existing checklist/procedure alongside the extracted facts and planned
   observations. Retain proposed/approved status. No new knowledge graph, large
   pattern library or inference that reading an entry means following it correctly.
4. **SV-10: isolate, then test the full result.** First compare extraction and
   audit behavior on frozen cases; then compare the complete plan and reviewer
   outputs. Keep the 13-label denominator, unsupported claims, false alarms and
   total cost including failures visible. Separate-case validation remains required
   before promotion. Reference answers stay outside agent context.

This proposal brings a small source-evidence part of SV-07 forward and adds a
bounded correction of rejected extraction. General semantic analysis repair needs
its own lineage design; SV-08 remains the deferred plan-only repair ticket.
Python can enforce the decisions here without introducing a manager model.
The full acceptance workload is unchanged. No runtime expansion or paid allocation
is approved by this research note.

Confidence is high in the documented architectural pattern and the observed local
gaps. Confidence in improvement on our workload is unestablished until evaluation.
Tool execution can validate a concrete design/check under declared assumptions;
it cannot prove that an omitted natural-language requirement was understood.
