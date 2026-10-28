# Testbench knowledge subchecklists

All entries are **proposed; none is engineering-approved**. TB06 incorporates engineering feedback and its revised wording needs confirmation. Original evidence and our proposed adaptations are identified separately. Use the [review template](REVIEW_TEMPLATE.md) to keep, correct or remove entries and state applicability.

The environment needs separate checklists for its capabilities. These seven groups contain **21 subchecks** for the planning agent to consider. They describe dependencies of proposed tests; they do not claim that a testbench is implemented or ready.

Background: [Accellera UVM 1.2 User Guide, sections 1.1.3–1.1.9](https://www.accellera.org/images/downloads/standards/uvm/uvm_users_guide_1.2.pdf), [OpenTitan UART environment](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/dv/README.md), and [PULP AXI verification components](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/README.md#simulation-only-modules). The subchecks are our proposed synthesis for engineering review.

## TB01 — Design hookup, clocks and reset

- **TB01.1:** Identify the exact design configuration, parameters, ports and interfaces under test.
- **TB01.2:** Provide the required clocks and reset sources; define valid timing, sequencing and observation windows.
- **TB01.3:** Confirm reset-domain ownership and how retained state is observed without illegal accesses.

**Why it matters:** Reset and configuration assumptions affect every downstream check.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?

## TB02 — Drive inputs and program registers

- **TB02.1:** Provide drivers or equivalent means to exercise each required interface, including legal configuration and register access.
- **TB02.2:** Support the boundary conditions, error injections and concurrent activity required by the selected tests.
- **TB02.3:** Document transaction completion, retry/backpressure handling and any sequence preconditions.

**Why it matters:** Generating a test idea requires a way to stimulate its conditions.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?

## TB03 — Observe transactions and state

- **TB03.1:** Provide monitors or equivalent observation for accepted transactions, output events and state transitions.
- **TB03.2:** Distinguish attempted inputs from accepted inputs, and account for buffering, latency and clock-domain boundaries.
- **TB03.3:** Expose the signals or registers needed by each pass/fail check; record any required debug access or instrumentation.

**Why it matters:** Checks require observations of actual behavior.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?

## TB04 — Expected behavior and automated checking

- **TB04.1:** Define the reference model or prediction rules from the approved specification; record unresolved behavior.
- **TB04.2:** Provide a scoreboard or equivalent comparison that matches expected and observed events with valid ordering/latency rules.
- **TB04.3:** Check that a deliberately wrong response is detected and a valid exception is accepted; document how checkers reset and flush.

**Why it matters:** A comparison is useful only when its predictor and matching rules are defined.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?

## TB05 — Protocol and temporal assertions

- **TB05.1:** List applicable protocol, ordering, ownership and timing properties with their assumptions and source references.
- **TB05.2:** Define assertion enable/disable conditions around reset and permitted exceptions.
- **TB05.3:** Demonstrate that each important checker can fail on a relevant violation and does not silently remain inactive.

**Why it matters:** Temporal and protocol constraints need explicit properties and assumptions.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?

## TB06 — Coverage and traceability

- **TB06.1:** Link each selected requirement to a check and its evidence. A self-checking test's pass/fail result can establish the specific scenario it exercised; assertion results or functional coverage may be appropriate for other checks. Identify requirements with no check. Do not require one covergroup per test.
- **TB06.2:** Choose the detail needed to establish the intended scope. For directed subsystem/SoC tests, a record of the checked condition, configuration and result may suffice. Define bins or cross-coverage only when needed to show that relevant boundaries or combinations occurred, particularly in randomized tests. Record justified exclusions; one passing scenario does not cover an entire feature's configurations.
- **TB06.3:** Check that the evidence is meaningful: required stimulus reached the checking point, the checker was enabled, and a skip or timeout cannot count as a pass. Where coverage is sampled, measure the specified event or completed/accepted behavior. Where formal assertions are used, record assumptions, reachability and proof status; a condition that never occurred does not establish that scenario was exercised.

**Why it matters:** Evidence should match the claimed behavior without adding coverage machinery that answers no useful question.

**Review basis:** [5a1aah's TB06 feedback](https://github.com/noobjam/Project-x/pull/4#issuecomment-6455313481), consistent with the alternative evidence methods in [K03](patterns.md#k03--separate-stimulus-choices-from-coverage-evidence). Revised wording still needs engineering confirmation.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?

## TB07 — Execution, diagnosis and ownership

- **TB07.1:** Provide a reproducible build/run entry point, tool versions, seeds/configuration and a basic smoke test.
- **TB07.2:** Define meaningful timeouts, failure reporting, logs and waveforms so a failed check can be reproduced and diagnosed.
- **TB07.3:** Assign owners to missing components and establish a regression list with agreed readiness evidence before relying on results.

**Why it matters:** Reproducible failures and clear ownership make tests actionable.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?
