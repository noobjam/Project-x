# Knowledge entry review template

Copy the block below into a comment on the review pull request. One comment can cover several related entries. Include exact IDs; untouched entries remain unreviewed.

```text
Reviewer / area of expertise:
Date:
Commit or PR revision reviewed:
Entry ID(s):

Decision: Keep / Correct / Remove / Need more information

Corrected wording or reason:
Source / section supporting this decision:
Applies when:
Exceptions or conditions where this should not be used:
Missing knowledge, subchecks or example cases:
Unresolved questions and the owner/evidence needed:

Suitable as agent guidance after these corrections? Yes / No / Pending
```

For a testbench group, identify the subcheck, for example `TB04.2`. For a worked example, assess starting conditions, stimulus, observation and pass/fail criteria. An unavailable testbench component should be recorded as a dependency.

For revision 2, use the [focused review questions](REVISION_NOTES.md). For each reusable example, also confirm what transfers to another design, what must be re-derived from its specification, and when the example is unsuitable. For TB06, choose sufficient evidence for the particular check; a covergroup per test is not mandatory.

For source disagreements, retain both references and identify the authority that resolves them. Do not approve an invented behavior simply to complete a row.

Add a closing comment if useful:

```text
Entries reviewed:
Entries suitable after the recorded corrections:
Entries requiring more evidence:
Highest-priority missing knowledge:
```

Approval is scoped to the named entries and conditions. It is not a claim that the agent generalizes to unseen designs or that proposed tests have run.
