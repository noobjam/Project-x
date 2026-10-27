# Testbench knowledge subchecklists

All entries are **proposed and unreviewed**. Original evidence and our proposed adaptations are identified separately. Use the [review template](REVIEW_TEMPLATE.md) to keep, correct or remove entries and state applicability.

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

- **TB06.1:** Map each selected requirement and test to an observation or coverage goal; identify uncovered requirements.
- **TB06.2:** Define the relevant boundary bins, configurations and interaction combinations, with justified exclusions.
- **TB06.3:** Check when coverage is sampled and ensure completed or accepted behavior is measured rather than merely attempted stimulus.

**Why it matters:** Attempted stimulus does not establish that a relevant condition occurred.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?

## TB07 — Execution, diagnosis and ownership

- **TB07.1:** Provide a reproducible build/run entry point, tool versions, seeds/configuration and a basic smoke test.
- **TB07.2:** Define meaningful timeouts, failure reporting, logs and waveforms so a failed check can be reproduced and diagnosed.
- **TB07.3:** Assign owners to missing components and establish a regression list with agreed readiness evidence before relying on results.

**Why it matters:** Reproducible failures and clear ownership make tests actionable.

**Use when:** When planning the corresponding environment capability; adapt to the project's chosen tools.

**For the engineer:** Which subchecks should change, what is missing, and when does this group apply?
