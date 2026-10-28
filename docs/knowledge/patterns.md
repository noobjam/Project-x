# Source-backed knowledge patterns

All entries are **proposed; none is engineering-approved**. K13–K15 adapt engineering contributions; their edited wording still needs confirmation. Original evidence and our proposed adaptations are identified separately. Use the [review template](REVIEW_TEMPLATE.md) to keep, correct or remove entries and state applicability.

## K01 — Trace every plan item to a versioned requirement

**Source family:** OpenHW. **Status:** proposed.

**Proposed reusable rule:** Record a source document, version and section for every feature to be verified.

**Why it matters:** A reviewer can check what the plan is claiming and whether a design change invalidates it.

**Use when:** Any specification-to-plan workflow.

**Concrete example / proposed adaptation:** For a reset test, cite the reset-domain definition and applicable interface table; leave a missing register definition visible.

**Limits and disagreements:** A valid citation is not proof that the proposed interpretation is correct.

**Source:** [openhw — docs/VerifPlans/VerificationPlanning101.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/VerificationPlanning101.md#L53-L54)

**Version:** 1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3. **Location:** lines 53–54.

**Source SHA-256:** `14f149d0caecd2d305e4b23fdbb49ca8659955491adcc22ae43db116876f97ec`.

<details>
<summary>Read the original source excerpt</summary>

````text
### Requirement Location
This is a pointer to the source Requirements document of the Features in question.  It can be a standards document, such as the RISC-V ISA, or a micro-architecture specification.   The CV32E40P [User Manual](https://cv32e40p.readthedocs.io/en/latest/intro/) lists sources of documentation relevant to the CV32E40P.  _Every item in a Verification Plan must be attributed to one or more of these sources_.  Please also include a chapter or section number.  Note that if you are using the [CV32E40P User Manual](https://core-v-docs-verif-strat.readthedocs.io/projects/cv32e40p_um/en/latest/) as a reference, you **must** provide a release/version number as well since this document is currently in active development.
````

</details>

**For the engineer:** What minimum provenance should our agent include in every knowledge-derived test?

## K02 — Select an actual pass/fail mechanism

**Source family:** OpenHW. **Status:** proposed.

**Proposed reusable rule:** State how a failure is detected: a self-checking result, signature, reference-model comparison, assertion or another justified mechanism.

**Why it matters:** Stimulus alone does not establish that the design behaved correctly.

**Use when:** Every executable test idea.

**Concrete example / proposed adaptation:** An arithmetic test can compare committed results against an instruction-set model; an interface-ordering rule can use a temporal checker.

**Limits and disagreements:** The named reference model or checker must exist or be listed as a dependency; a method name alone does not demonstrate feasibility.

**Source:** [openhw — docs/VerifPlans/VerificationPlanning101.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/VerificationPlanning101.md#L67-L75)

**Version:** 1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3. **Location:** lines 67–75.

**Source SHA-256:** `14f149d0caecd2d305e4b23fdbb49ca8659955491adcc22ae43db116876f97ec`.

<details>
<summary>Read the original source excerpt</summary>

````text
### Pass/Fail Criteria
Here we attempt to answer the question, "how will the testbench know the test passed?".  There are several methods that are typically used in CORE-V projects, and it is common to use more than one for a given item in a Verification Plan.
* **Self Checking**: A self-checking test-program encodes the correct result directly into the testcase and compares what the DUT does against this "known good" outcome.  See the [RISCY Testcases](https://core-v-docs-verif-strat.readthedocs.io/en/latest/pulp_verif.html#ri5cy-testcases) section of the Verification Strategy for an example of this.  This strategy is used extensively by the RISC-V Foundation Compliance tests.
* **Signature Check**: This is a more sophisitcated form of a self checking test-program.  The results of the test are used to calculate a signature and this is compared against a "known good" signature.  This strategy is also used by the RISC-V Foundation Compliance tests.
* **Check against RM**: Here, the test-program does not "know" the correct output of the test.  Instead, the pass/fail criteria is determined by a **_Reference Model_** (RM).  An RM is a verification environment (testbench) component which models some or all of the DUT behavior.  The verification environment must compare the actual results from the DUT and the expected results from the RM.  When practical, this is the preferred approach because it makes testcase maintenance simplier.
* **Assertion Check**: Failure is detected by an assertion, typically coded in SVA.
* **Any/All**: Any (or all) of the above pass/fail criteria can be reasonably assumed to catch a non-compliance of a specific feature/requirement.
* **Other**: If one of the above Pass/Fail Criteria does not fit your needs, specify it here.
* **N/A**: Select this for those (rare) features in the specification do not have side effects that are observable in a functional simulation of an RTL model.
````

</details>

**For the engineer:** Which check mechanisms are appropriate for our project, and how should missing checkers be recorded?

## K03 — Separate stimulus choices from coverage evidence

**Source family:** OpenHW. **Status:** proposed.

**Proposed reusable rule:** Identify the test type and separately identify how the required feature or condition will be shown to have occurred.

**Why it matters:** Running a random test does not guarantee that a selected corner case happened.

**Use when:** Plans with directed or randomized tests.

**Concrete example / proposed adaptation:** A directed test can explicitly reach and check a selected threshold, recording its configuration and pass/fail result. A randomized test may need counters or bins to establish which threshold cases actually occurred. Choose the evidence per requirement; a covergroup per test is not mandatory.

**Limits and disagreements:** Do not inherit a source project's coverage closure threshold or treat code coverage alone as functional completeness. The quoted guide prefers functional coverage; that is its methodology preference, not a universal requirement. Following [5a1aah's TB06 feedback](https://github.com/noobjam/Project-x/pull/4#issuecomment-6455313481), directed subsystem/SoC checks may use meaningful pass/fail records. Such a record supports only the behavior and configurations actually checked; skipped checks and an idle assertion cannot establish exercised scenarios.

**Source:** [openhw — docs/VerifPlans/VerificationPlanning101.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/VerificationPlanning101.md#L76-L83)

**Version:** 1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3. **Location:** lines 76–83.

**Source SHA-256:** `14f149d0caecd2d305e4b23fdbb49ca8659955491adcc22ae43db116876f97ec`.

<details>
<summary>Read the original source excerpt</summary>

````text
### Test Type
Choose one or more of the following:
* **RISC-V Compliance**: a self-checking ISA compliance testcase from the RISC-V Foundation.
* **Directed Self-Checking**: a directed (non-random) self-checking testcase from the OpenHW Group that is not specifically targetting ISA compliance.
* **Directed Non-Self-Checking**: a directed (non-random) non-self-checking testcase from the OpenHW Group that is not specifically targetting ISA compliance.  Note that these tests assume that the pass/fail criteria will be "Check against ISS" (or other reference model).
* **Constrained-Random**: a constrained-random testcase.  Typically the stimulus for these will come from the Google random instruction stream generator.  Note that by defintion these tests cannot be self-checking.
* **ENV capability, not specific test**: Often, a specific feature is not specifically covered by a specific test or check.  For example, an assertion checking for bus protocol errors could reasonably expect to cause a failure with any type of test.
* **Other**: If one of the above Test Types does not fit your needs, specify it here.
````

</details>

**Source:** [openhw — docs/VerifPlans/VerificationPlanning101.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/VerificationPlanning101.md#L84-L89)

**Version:** 1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3. **Location:** lines 84–89.

**Source SHA-256:** `14f149d0caecd2d305e4b23fdbb49ca8659955491adcc22ae43db116876f97ec`.

<details>
<summary>Read the original source excerpt</summary>

````text
### Coverage Method
How will we know that the Feature is verified (covered)?  There are several choices here:
* **Testcase:** if the testcase was run, the Feature was tested.
* **Functional Coverage:** the testbench supports SystemVerilog cover_groups that measures stimulus/configuration/response conditions to show that the Feature was tested.  **This is the perferred method of coverage.**
* **Assertion Coverage**: an alternate form of functional coverage, implemented as SVA cover properties.
* **Code Coverage:** the Feature is deemed to be tested when the specific conditions in the RTL have been exercised.
````

</details>

**For the engineer:** Which coverage records would make a generated plan useful to you?

## K04 — Use an authored instruction plan without importing its mistakes

**Source family:** OpenHW + RISC-V. **Status:** proposed.

**Proposed reusable rule:** Use register combinations, operand values and result observations as planning dimensions, while taking instruction semantics from the applicable ISA specification.

**Why it matters:** Even documents from one credible project can disagree; authoritative behavior must be resolved before reuse.

**Use when:** Processor instruction planning with a known ISA and implementation configuration.

**Concrete example / proposed adaptation:** For ADDI, review source/destination combinations, same-register cases, positive/negative/zero operands and the reference-model check. Confirm XLEN and sign extension from the ISA.

**Limits and disagreements:** The introductory OpenHW example talks about overflow being flagged, but its actual RV32I plan says overflow is ignored. The RISC-V manual agrees with the plan. Do not transfer the introductory overflow wording or RV32-specific assumptions into a new design.

**Source:** [openhw — docs/VerifPlans/ISA/RV32/Simulation/RV32I_Base_Instructions.xlsx](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/ISA/RV32/Simulation/RV32I_Base_Instructions.xlsx)

**Version:** 1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3. **Location:** Sheet RV32I, cells A3:I5.

**Source SHA-256:** `35a99d9080e6235fa1d626c217345b2c3fecf8c92aaaa10dccd127e724376815`.

<details>
<summary>Read the original source excerpt</summary>

````text
A3: ISA
Chapter 2.4

B3: RV32I
Register-Immediate Instructions

C3: ADDI

D3: addi rd, rs1, imm[11:0]
rd = rs1 + Sext(imm[11:0])
Arithmetic overflow is lost and ignored


E3: Register operands:

All possible rs1 registers are used.
All possible rd registers are used.
All possible register combinations where rs1 == rd are used

F3: Check against ISS

G3: Constrained-Random

H3: Functional Coverage

I3: isacov.rv32i_addi_cg.cp_rs1
isacov.rv32i_addi_cg.cp_rd
isacov.rv32i_addi_cg.cp_rd_rs1_hazard

E4: Input operands:

rs1 value is +ve, -ve and zero
immi value is +ve, -ve and zero
All combinations of rs1 and immi +ve, -ve, and zero values are used
All bits of rs1 are toggled
All bits of immi are toggled


F4: Check against ISS

G4: Constrained-Random

H4: Functional Coverage

I4: isacov.rv32i_addi_cg.cp_rs1_value
isacov.rv32i_addi_cg.cp_immi_value
isacov.rv32i_addi_cg.cross_rs1_immi_value
isacov.rv32i_addi_cg.cp_rs1_toggle
isacov.rv32i_addi_cg.cp_immi_toggle

E5: Output result:

rd value is +ve, -ve and zero
All bits of rd are toggled

F5: Check against ISS

G5: Constrained-Random

H5: Functional Coverage

I5: isacov.rv32i_addi_cg.cp_rd_value
isacov.rv32i_addi_cg.cp_rd_toggle
````

</details>

**Source:** [openhw — docs/VerifPlans/VerificationPlanning101.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/VerificationPlanning101.md#L31-L50)

**Version:** 1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3. **Location:** lines 31–50.

**Source SHA-256:** `14f149d0caecd2d305e4b23fdbb49ca8659955491adcc22ae43db116876f97ec`.

<details>
<summary>Read the original source excerpt</summary>

````text
## A Trivial Example: the RV32I ADDI Instruction
Let's assume your task is to verify a core's implementation of the RV32I ADDI instruction.  Simple right?  Create a simple assembler program with a few **_addi_** instructions check the results and we're done.  Unfortunately, simply checking for the correct result (rd = rs1 + imm), of a few instructions is insufficent.  We also need to check:
* Overflow is detected and flagged correctly
* Underflow is detected and flagged correctly
* No instruction execution side-effects (e.g. unexpected GPR changes, unexpected condition codes)
* Program counter updates appropriately

Doing this exhaustively is impractical.  With one 32-bit and one 12-bit operand there are approximately 1.8\*10^13 unique sums that can be calculated. In [big-oh](https://rob-bell.net/2009/06/a-beginners-guide-to-big-o-notation/) notation that is O(13). Including the cross-products of source and destination register yields O(16) unique instructions simply to fully verify addi.  Obviously this is impractical and one of the things that makes Verification an art is determing the minimal amount of coverage to have confidence that a feature is sufficiently tested.  If we make a few simplifying assumptions we can reduce the problem to a managible size: for example we could say that addi is fully verified by covering the following cases:

* Use x0..x31 as rs1
* Use x0..x31 as rd (Note: the result of this operation will always be 0x00000000 when rd is x0)
* Set/Clear all bits of immediate
* Set/Clear all bits of rs1
* Set/Clear all bits of rd

It is the opinion of the author that the list above is sufficient for the addi instruction.  You may see it as overkill or underkill depending on your understanding of the micro-architecture or your level of risk adversion.

The key point is that taking the time to specify a Testplan for each feature in the device-under-test forces us to think about what the feature does, what we need to check to ensure its functions correctly and what stimulus and configuration needs to be covered to ensure the feature is tested under all penitent conditions.

The template used for this project attempts to provide an easy-to-use format to capture and review this information for every feature in the design.
````

</details>

**Source:** [riscv — RISC-V Unprivileged ISA Manual](https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf)

**Version:** Confirm the ISA revision used by the target design. **Location:** Integer Register-Immediate Instructions / ADDI.

<details>
<summary>Read the original source excerpt</summary>

````text
Arithmetic overflow is ignored
````

</details>

**For the engineer:** Confirm the semantic correction, then curate which operand and register combinations are needed for our target.

## K05 — Break the environment into stimulus, observation and checking

**Source family:** Accellera. **Status:** proposed.

**Proposed reusable rule:** Identify the driver, monitor, sequencer and checking roles a test depends on; group them by interface and environment.

**Why it matters:** One testbench-ready checkbox hides independent missing capabilities.

**Use when:** UVM-based environments; adapt equivalent roles for other frameworks.

**Concrete example / proposed adaptation:** A bus-reset test needs a way to drive traffic, control reset, monitor accepted traffic and check the permitted post-reset result.

**Limits and disagreements:** These are UVM 1.2 methodology roles. They do not require our planning agent itself to be implemented as a UVM agent or prove compatibility with every current UVM release.

**Source:** [accellera — uvm_users_guide_1.2.pdf](https://www.accellera.org/images/downloads/standards/uvm/uvm_users_guide_1.2.pdf)

**Version:** UVM 1.2 User Guide, October 8 2015. **Location:** Sections 1.1.3–1.1.9; printed pages 2–4. Read the supplied guide for original descriptions..

**Source SHA-256:** `6cddf735c3f7f700ef5f62b2954a28f7fb7e590a149314cbe5b0d342f99d131c`.

Read the cited section in the original document; the guidance above is our proposed adaptation.

**For the engineer:** Review the seven testbench subchecklists and add any missing capability or hierarchy.

## K06 — Make expected-versus-observed comparison explicit

**Source family:** Accellera. **Status:** proposed.

**Proposed reusable rule:** Define how observed inputs feed a predictor and how expected outputs are matched to actual outputs.

**Why it matters:** The reference calculation and the observation path can each be incomplete or wrong.

**Use when:** Tests relying on a scoreboard or reference model.

**Concrete example / proposed adaptation:** For a receive buffer, track accepted items and compare output contents, while treating reset and dropped overflow items according to the specification.

**Limits and disagreements:** The reference behavior, matching/ordering rules and allowed latency are design-specific; the UVM guide does not supply them for our design.

**Source:** [accellera — uvm_users_guide_1.2.pdf](https://www.accellera.org/images/downloads/standards/uvm/uvm_users_guide_1.2.pdf)

**Version:** UVM 1.2 User Guide, October 8 2015. **Location:** Section 1.1.4 UVM Scoreboard; printed page 2. Source summary above; no verbatim excerpt..

**Source SHA-256:** `6cddf735c3f7f700ef5f62b2954a28f7fb7e590a149314cbe5b0d342f99d131c`.

Read the cited section in the original document; the guidance above is our proposed adaptation.

**For the engineer:** What would a useful predictor/checker description contain in our generated plans?

## K07 — Exercise variable response delay and constrained traffic

**Source family:** PULP. **Status:** proposed.

**Proposed reusable rule:** Plan configurable response delays and constrained randomized traffic when testing a bus component.

**Why it matters:** Fixed-latency examples can miss interactions between stalled and concurrent traffic.

**Use when:** AXI or AXI-Lite components whose documented behavior includes variable-latency handshakes.

**Concrete example / proposed adaptation:** Send a chosen transaction set while varying peer delays, then verify accepted transactions and permitted responses using the target's ordering rules.

**Limits and disagreements:** PULP provides reusable drivers and random peers; their presence does not specify our DUT's ordering, timeout or fairness guarantees.

**Source:** [pulp — README.md](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/README.md#L89-L109)

**Version:** 70b8e54fd460e3308e58be596ceb3566a6e3576e. **Location:** lines 89–109.

**Source SHA-256:** `9a8390200dee89eb56763f485145da896ac02c6c06eb12fdf7fbc2bbdca2eeb4`.

<details>
<summary>Read the original source excerpt</summary>

````text
### Simulation-Only Modules

In addition to the modules above, which are available in synthesis and simulation, the following modules are available only in simulation.  Those modules are widely used in our testbenches, but they are also suitable to build testbenches for AXI modules and systems outside this repository.

| Name                                                 | Description                                                                                            |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| [`axi_chan_compare`](src/axi_chan_compare.sv)        | Non-synthesizable module comparing two AXI channels of the same type                                   |
| [`axi_chan_logger`](src/axi_test.sv)                 | Logs the transactions of an AXI4(+ATOPs) port to files.                                                |
| [`axi_driver`](src/axi_test.sv)                      | Low-level driver for AXI4(+ATOPs) that can send and receive individual beats on any channel.           |
| [`axi_dumper`](src/axi_dumper.sv)                    | Dumps log to file to be interpreted by `axi_dumper_interpret` script for debugging purposes.           |
| [`axi_file_master`](src/axi_test.sv)                 | AXI4 master for file-based testbenches                                                                 |
| [`axi_lite_driver`](src/axi_test.sv)                 | Low-level driver for AXI4-Lite that can send and receive individual beats on any channel.              |
| [`axi_lite_rand_master`](src/axi_test.sv)            | AXI4-Lite master component that issues random transactions within user-defined constraints.            |
| [`axi_lite_rand_slave`](src/axi_test.sv)             | AXI4-Lite slave component that responds to transactions with constrainable random delays and data.     |
| [`axi_rand_master`](src/axi_test.sv)                 | AXI4(+ATOPs) master component that issues random transactions within user-defined constraints.         |
| [`axi_rand_slave`](src/axi_test.sv)                  | AXI4(+ATOPs) slave component that responds to transactions with constrainable random delays and data.  |
| [`axi_scoreboard`](src/axi_test.sv)                  | Scoreboard that models a memory that only gets changed by the monitored AXI4(+ATOPs) port.             |
| [`axi_sim_mem`](src/axi_sim_mem.sv)                  | Infinite memory with AXI4 slave port.                                                                  |



````

</details>

**For the engineer:** Which delay, backpressure and concurrency combinations matter for our interfaces?

## K08 — Use a transaction-derived memory reference model

**Source family:** PULP. **Status:** proposed.

**Proposed reusable rule:** Maintain expected memory contents from monitored bus activity and compare subsequent observations against it.

**Why it matters:** Checks must follow the transactions actually accepted, including byte enables and ordering rules.

**Use when:** Memory-mapped interfaces with well-defined read/write semantics.

**Concrete example / proposed adaptation:** Write distinguishable patterns through accepted transactions; read selected addresses back and check against the resulting memory model.

**Limits and disagreements:** Side-effecting registers, speculative activity, atomic operations and multiple writers may require a different predictor.

**Source:** [pulp — README.md](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/README.md#L89-L109)

**Version:** 70b8e54fd460e3308e58be596ceb3566a6e3576e. **Location:** lines 89–109.

**Source SHA-256:** `9a8390200dee89eb56763f485145da896ac02c6c06eb12fdf7fbc2bbdca2eeb4`.

<details>
<summary>Read the original source excerpt</summary>

````text
### Simulation-Only Modules

In addition to the modules above, which are available in synthesis and simulation, the following modules are available only in simulation.  Those modules are widely used in our testbenches, but they are also suitable to build testbenches for AXI modules and systems outside this repository.

| Name                                                 | Description                                                                                            |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| [`axi_chan_compare`](src/axi_chan_compare.sv)        | Non-synthesizable module comparing two AXI channels of the same type                                   |
| [`axi_chan_logger`](src/axi_test.sv)                 | Logs the transactions of an AXI4(+ATOPs) port to files.                                                |
| [`axi_driver`](src/axi_test.sv)                      | Low-level driver for AXI4(+ATOPs) that can send and receive individual beats on any channel.           |
| [`axi_dumper`](src/axi_dumper.sv)                    | Dumps log to file to be interpreted by `axi_dumper_interpret` script for debugging purposes.           |
| [`axi_file_master`](src/axi_test.sv)                 | AXI4 master for file-based testbenches                                                                 |
| [`axi_lite_driver`](src/axi_test.sv)                 | Low-level driver for AXI4-Lite that can send and receive individual beats on any channel.              |
| [`axi_lite_rand_master`](src/axi_test.sv)            | AXI4-Lite master component that issues random transactions within user-defined constraints.            |
| [`axi_lite_rand_slave`](src/axi_test.sv)             | AXI4-Lite slave component that responds to transactions with constrainable random delays and data.     |
| [`axi_rand_master`](src/axi_test.sv)                 | AXI4(+ATOPs) master component that issues random transactions within user-defined constraints.         |
| [`axi_rand_slave`](src/axi_test.sv)                  | AXI4(+ATOPs) slave component that responds to transactions with constrainable random delays and data.  |
| [`axi_scoreboard`](src/axi_test.sv)                  | Scoreboard that models a memory that only gets changed by the monitored AXI4(+ATOPs) port.             |
| [`axi_sim_mem`](src/axi_sim_mem.sv)                  | Infinite memory with AXI4 slave port.                                                                  |



````

</details>

**For the engineer:** Which interfaces permit this model and which need special handling?

## K09 — Check optional-feature compatibility at integration boundaries

**Source family:** PULP. **Status:** proposed.

**Proposed reusable rule:** Identify unsupported optional protocol features, required filters and legal signal values before connecting components.

**Why it matters:** Individually valid components can be incompatible when integrated.

**Use when:** Systems using PULP AXI modules or an analogous explicitly specified optional protocol feature.

**Concrete example / proposed adaptation:** For an ATOP-capable master facing a non-supporting slave, check the documented filtering and response responsibilities rather than assuming ordinary-write behavior.

**Limits and disagreements:** PULP's AXI4+ATOP rules are specific to that extension. Confirm our actual protocol and supported features before applying them.

**Source:** [pulp — README.md](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/README.md#L110-L124)

**Version:** 70b8e54fd460e3308e58be596ceb3566a6e3576e. **Location:** lines 110–124.

**Source SHA-256:** `9a8390200dee89eb56763f485145da896ac02c6c06eb12fdf7fbc2bbdca2eeb4`.

<details>
<summary>Read the original source excerpt</summary>

````text
## Atomic Operations

AXI4+ATOPs means the full AXI4 specification plus atomic operations (ATOPs) as defined in Section E1.1 of the [AMBA 5 specification][AMBA 5 Spec]. This has the following implications for modules that do not implement ATOPs and systems that include such modules:

- Masters that do not issue ATOPs must set `aw_atop` to `'0`.
- Slaves that do not support ATOPs must specify this in their interface documentation and can ignore the `aw_atop` signal.
- System designers are responsible for ensuring that
  1. slaves that do not support ATOPs are behind an [`axi_atop_filter`](src/axi_atop_filter.sv) if any master could issue an ATOP to such slaves and
  2. the `aw_atop` signal is well-defined at the input of any (non-AXI4-Lite) module in this repository.

Masters and slaves that do support ATOPs must adhere to Section E1.1 of the [AMBA 5 specification][AMBA 5 Spec].  In particular:
- ATOPs that have the `aw_atop[axi_pkg::ATOP_R_RESP]` bit set generate a write response (B channel) beat and at least one read response (R channel) beat.  All modules for which the `aw_atop[axi_pkg::ATOP_R_RESP]` bit could be set at their master port must be able to handle both B and R beats (in any order and without requiring a simultaneous handshake) for each such ATOP request.  All modules for which the `aw_atop[axi_pkg::ATOP_R_RESP]` bit could be set at their slave port must respond with the appropriate number of B and R beats for each such ATOP request.
- ATOPs must not use the same AXI ID as any other transaction that is outstanding at the same time.


````

</details>

**For the engineer:** Which optional interface features and compatibility checks belong in our knowledge base?

## K10 — Inject a defined receive error and observe its notification

**Source family:** OpenTitan. **Status:** proposed.

**Proposed reusable rule:** Include targeted error injection with an explicit error observation and recovery check where specified.

**Why it matters:** Normal traffic cannot establish whether a documented error is detected.

**Use when:** Interfaces with defined integrity or framing errors.

**Concrete example / proposed adaptation:** OpenTitan's UART parity-error testpoint varies parity configuration, injects a bad parity bit and checks the interrupt.

**Limits and disagreements:** Error-bit encoding, masking, clearing and recovery behavior must come from the current interface specification.

**Source:** [opentitan — hw/ip/uart/data/uart_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart_testplan.hjson#L43-L49)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 43–49.

**Source SHA-256:** `0c1288ba944faf969aafa8a03f63e4b67e421ecbc28b03870bf1de766e55fcd0`.

<details>
<summary>Read the original source excerpt</summary>

````text
      name: parity_error
      desc: '''
            - Enable parity and randomly set even/odd parity
            - Inject parity error randomly on data sent from rx and ensure the interrupt is
              raised'''
      stage: V2
      tests: ["uart_rx_parity_err", "uart_intr"]
````

</details>

**For the engineer:** Which error classes and notification/recovery checks are relevant to our design?

## K11 — Reset during activity and verify recovery

**Source family:** OpenTitan. **Status:** proposed.

**Proposed reusable rule:** Exercise reset around active transfers and then check that the documented normal operation resumes.

**Why it matters:** Reset can leave monitors, predictors and in-flight work inconsistent if the plan does not address their state.

**Use when:** Resettable interfaces with specified behavior for in-flight transactions.

**Concrete example / proposed adaptation:** OpenTitan's I2C error-interrupt sequence injects a bus disturbance, checks the error, resets the environment on the fly and resumes transactions.

**Limits and disagreements:** The source test resets DUT, peer and scoreboard together; that is one test strategy, not proof that all reset-domain combinations are covered.

**Source:** [opentitan — hw/ip/i2c/data/i2c_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/i2c/data/i2c_testplan.hjson#L39-L60)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 39–60.

**Source SHA-256:** `7c7f8e85c34989c2720213e6135fc27a242d4538ce4e23c20a24a14c464da0cf`.

<details>
<summary>Read the original source excerpt</summary>

````text
      name: host_error_intr
      desc: '''
            Test error interrupts are asserted by the Host DUT due to
            interference and unstable signals on bus.

            Stimulus:
              - Configure DUT/Agent to Host/Target mode respectively
              - In host transmit mode, device (target/host) forces SDA or SCL signal low within the
                clock pulse of host SCL that asserts `sda_interference` or `scl_interference`
                interrupts
              - In host receiving mode (data or ack bits), SDA signal is changed with the
                clock pulse of host SCL that asserts `intr_sda_unstable` interrupts
              - When error interrupt assertions are detected, dut, agent, and scoreboard will be
                reset on-the-fly then new transaction can be continue programming

            Checking:
              - Ensure all intr_scl_interference, intr_sda_interference, and
                intr_sda_unstable interrupts are asserted and stay asserted until cleared
              - Ensure IP operation get back normal after on-the-fly reset finished
            '''
      stage: V2
      tests: ["i2c_host_error_intr"]
````

</details>

**For the engineer:** Which components should reset together, and which independent reset cases need separate coverage?

## K12 — Resolve specification–testplan disagreements before reuse

**Source family:** OpenTitan. **Status:** proposed.

**Proposed reusable rule:** Treat an authored testplan as evidence to inspect, and verify behavior against the matching specification and configuration.

**Why it matters:** A credible repository can contain stale descriptions or inconsistent documents at the same revision.

**Use when:** Any knowledge imported from a project with multiple design and verification documents.

**Concrete example / proposed adaptation:** Keep the reusable boundary-testing idea, but require the engineer to reconcile interrupt clearing and FIFO-depth statements before promoting the detailed example.

**Limits and disagreements:** The pinned UART testplan calls watermark interrupts sticky, while its theory document describes level status that cannot be cleared while the condition holds. The FIFO test descriptions also mention 32 bytes while the pinned RX design specifies 64. These are unresolved curation findings, not approved portable behavior.

**Source:** [opentitan — hw/ip/uart/data/uart_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart_testplan.hjson#L52-L62)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 52–62.

**Source SHA-256:** `0c1288ba944faf969aafa8a03f63e4b67e421ecbc28b03870bf1de766e55fcd0`.

<details>
<summary>Read the original source excerpt</summary>

````text
      name: watermark
      desc: '''
            - Program random tx/rx fifo watermark level and keep sending random tx/rx data
              to fifo.
            - As the number of pending data entries in the tx/rx fifo reaches the programmed
              watermark level (fifo size >= watermark level), ensure that the watermark interrupt
              is asserted
            - Ensure interrupt stays asserted until cleared as well as fifo level dropped.
              The tx/rx watermark interrupt is sticky'''
      stage: V2
      tests: ["uart_tx_rx", "uart_intr"]
````

</details>

**Source:** [opentitan — hw/ip/uart/data/uart_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart_testplan.hjson#L71-L78)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 71–78.

**Source SHA-256:** `0c1288ba944faf969aafa8a03f63e4b67e421ecbc28b03870bf1de766e55fcd0`.

<details>
<summary>Read the original source excerpt</summary>

````text
      name: fifo_overflow
      desc: '''
            - Keep sending over 32 bytes of data over tx/rx fifo
            - Ensure excess data bytes are dropped and check overflow interrupt
            - This uart_fifo_overflow_vseq is extent from uart_fifo_full_vseq and override the
              constraint to be able to send data over fifo size'''
      stage: V2
      tests: ["uart_fifo_overflow"]
````

</details>

**Source:** [opentitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L132-L141)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 132–141.

**Source SHA-256:** `6f9e15b9af2a77c41ee77717c87287a14635c84f6b3e6f2a7bec708628d77ba6`.

<details>
<summary>Read the original source excerpt</summary>

````text
#### tx_watermark / tx_empty / rx_watermark

If the TX FIFO level becomes smaller than the TX water mark level (configurable via [`FIFO_CTRL.TXILVL`](registers.md#fifo_ctrl--txilvl)), the `tx_watermark` interrupt is raised to inform SW.
If the TX FIFO is empty, the `tx_empty` interrupt is raised to inform SW.
If the RX FIFO level becomes greater than or equal to RX water mark level (configurable via [`FIFO_CTRL.RXILVL`](registers.md#fifo_ctrl--rxilvl)), the `rx_watermark` interrupt is raised to inform SW.

Note that the watermark interrupts and the empty interrupt are level-based status interrupts.
They will stay asserted for as long as the FIFO levels are in violation of the configured level and cannot be cleared by writing to the status register.
This also means that `tx_watermark` and `tx_empty` start off in an asserted state (reset high).

````

</details>

**Source:** [opentitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L57-L94)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 57–94.

**Source SHA-256:** `6f9e15b9af2a77c41ee77717c87287a14635c84f6b3e6f2a7bec708628d77ba6`.

<details>
<summary>Read the original source excerpt</summary>

````text
### Reception

The RX module oversamples the RX input pin at 16x the requested baud clock.
When the input is detected low the receiver will check half a bit-time later (i.e. 8 cycles of the oversample clock) that the line is still low before detecting the START bit.
If the line has returned high the glitch is ignored.
After it detects the START bit, the RX module samples at the center of each bit-time and gathers incoming serial bits into a character buffer.
If the STOP bit is detected as high and the optional parity bit is correct the data byte is pushed into a 64-byte RX FIFO.
The data can be read out by reading the [`RDATA`](registers.md#rdata) register.

This behavior of the receiver can be used to compute the approximate baud clock frequency error that can be tolerated between the transmitter at the other end of the cable and the receiver.
The initial sample point is aligned with the center of the START bit.
The receiver will then sample every 16 cycles of the oversampling clock, the diagram below shows the number of ticks after the centering that each bit is captured.
Because of the frequency difference between the transmitter and receiver the actual sample point will drift compared to the ideal center of the bit.
In order to correctly receive the STOP bit it must be sampled between the "early" and "late" points shown on the diagram, which are half a bit-time or 8 ticks of the 16x baud clock before or after the center.
If the transmitter is considered "ideal", then the local clock must thus differ by no more than plus or minus 8 ticks in 144, or approximately +/- 5.5%.
If parity is enabled the stop bit will be a bit time later, so this becomes 8/160, or about +/- 5%.

```wavejson
{
  signal: [
    { name: 'Sample', wave: '', node: '..P............', period: "2" },
    {},
    { name: 'rx',
      wave: '1.0.3.3.3.3.3.3.3.3.1.0.3',
      node: '...A................C.D..',
      cdata: [ "idle", "start", "+16", "+32", "+48", "+64", "+80",
                "+96", "+112", "+128", "+144", "next start" ] },
  ],
    "edge"   : ["P-|>A center", "P-|>C early", "P-|>D late"],
  head: {
    text: 'Receiver sampling window',
  },
}
```

In practice, the transmitter and receiver will both differ from the ideal baud rate.
Since the worst case difference for reception is 5%, the uart can be expected to work if both sides are within +/- 2.5% of the ideal baud rate.

````

</details>

**For the engineer:** Which source governs these details, and what correction should we retain in the knowledge entry?

## K13 — Plan clock and reset connectivity checks from the specification

**Source family:** Engineer-contributed SoC integration practice. **Status:** proposed adaptation, confirmation pending.

**Provenance:** [5a1aah's clock/reset proposal](https://github.com/noobjam/Project-x/pull/4#issuecomment-6454839896), 27 October 2026. This condensed planning rule preserves the proposed method and limits; it does not validate the comment's executable assertion examples. [E15](examples.md#e15--separate-reset-release-from-permission-to-boot) and [E18](examples.md#e18--account-for-clock-domains-without-inventing-timing) supply independent public specification cases.

**Proposed reusable rule:** Build a specification-derived clock/reset connection table. For each in-scope block input, identify the source, destination, mode, expected relation and source reference. Include explicitly forbidden connections. Use the table to propose connectivity checks and to expose missing specifications.

**Use when:** A subsystem or SoC integrates multiple clock/reset domains, clock gates, reset controllers or functional/test-mode selections.

**Required inputs:** Versioned clock/reset architecture, mode definitions, polarity, reset ownership and specified timing. RTL port inventories can help detect missing endpoints; they cannot supply the expected wiring. RTL/netlist access, formal tooling and observation points are execution dependencies, not assumed agent capabilities.

**Planning procedure:**

1. Record each path using the following fields. Keep undefined cells unresolved.

   | Source | Destination | Mode/condition | Expected relation | Spec location | Check/evidence | Open question |
   | --- | --- | --- | --- | --- | --- | --- |
   | Spec-defined source | Spec-defined block input | Functional, test or power mode | Direct, inverted, constant, muxed, specified delay, or forbidden | Document/revision/section | Proposed method and required access | Missing mode, endpoint or timing |

2. Account for every in-scope clock/reset input, or record a justified exclusion. Check polarity, mode selection and unintended reset ownership. Use inventory comparisons to find omissions, not to manufacture specification facts.
3. Choose formal connectivity, simulation assertions or directed observation according to available evidence and tools. Check that each condition can occur. Simulation establishes only the exercised cases; a formal result is conditional on its model, assumptions and proof status.
4. If gates, PLLs or synchronizers are abstracted, record the boundaries and separate qualification needed for their behavior. Reset release timing must come from the specification and sampling model; synchronizer depth alone does not justify an unconditional exact-cycle claim.
5. Plan separate frequency/ratio, reset sequencing or clock-switch checks where specified. Review changed paths after integration or DFT changes when those stages are in scope.

**Evidence to request:** A reviewed path table, endpoint omissions/exclusions, method and assumptions per path, and eventual check results. Record unreachable conditions, incomplete proofs and missing timing explicitly. A completed plan is not a claim that these checks have run.

**Limits:** Logical connectivity does not establish clock quality, timing closure or safe clock/reset domain crossing. Power-dependent behavior needs the applicable power intent. A table derived solely from the same database that generated the implementation can share its errors. Do not promise a fixed runtime or exhaustive verification of the entire design.

**For the engineer:** Confirm the required table fields, acceptable methods and exclusions. Which clock/reset modes are routinely absent from your input specifications?

## K14 — Check data and control connections in each specified mode

**Source family:** Engineer-contributed SoC integration practice. **Status:** proposed adaptation, confirmation pending.

**Provenance:** [5a1aah's data/control proposal](https://github.com/noobjam/Project-x/pull/4#issuecomment-6454839896), 27 October 2026. [E16](examples.md#e16--trace-an-event-through-a-two-level-interrupt-map) illustrates why a system connection may require more than a direct-wire check.

**Proposed reusable rule:** Turn interrupt, DMA, pinmux, configuration, strap, debug and power-control maps into conditional source-to-destination checks. Preserve bit mappings, reductions, tie-offs, permitted delays and prohibited paths exactly as specified.

**Use when:** Independently verified IPs are connected at subsystem/SoC level, or integration settings select different routes.

**Required inputs:** Signal/interrupt maps, mode and mux tables, interface definitions, latency rules and security/power constraints where relevant. Record absent inputs rather than copying current RTL behavior into the expectation.

**Planning procedure:**

1. Use the K13 table format, adding bit mapping/width and any handshake rule. Account for in-scope endpoints and justified exclusions; do not turn every internal net into an LLM-generated test row.
2. Group equivalent connections into parameterized checks. For a vector mapping, stimulate one source bit at a time and check all relevant destinations, including those that should remain inactive. This can distinguish swaps, shifts and unintended fan-out.
3. Exercise each specified mux selection, default, gating condition and tie-off. Undefined reserved selections remain open questions.
4. State whether the stimulus forces an integration boundary or triggers the real peripheral event. A forced signal can check wiring but does not establish that the peripheral generates the event correctly.
5. Separate direct/registered wiring from functional behavior such as queues, arbitration, interrupt acknowledgement or variable-latency handshakes. Use the corresponding behavior's specification to define those expectations.

**Evidence to request:** A result for each selected path/condition, the observation points and a list of unexercised or excluded cases. Directed pass/fail records may suffice under [TB06](testbench-checklists.md#tb06--coverage-and-traceability); additional coverage is chosen for a purpose.

**Limits:** Correct connections do not establish correct feature operation, bus protocol behavior or safe domain crossing. A structural absence of a wire is not proof that secret data cannot affect an output through other logic. Formal checks require explicit assumptions and reachable conditions; simulation covers its exercised cases. Power isolation and post-DFT behavior need their own applicable context.

**For the engineer:** Confirm which connection families belong in the initial knowledge set, how to group repetitive paths, and which cases require functional rather than wiring checks.

## K15 — Verify register policies and cover excluded special behavior

**Source family:** Engineer-contributed register verification practice; Accellera UVM register methodology. **Status:** proposed adaptation, confirmation pending.

**Provenance:** [5a1aah's register proposal](https://github.com/noobjam/Project-x/pull/4#issuecomment-6454839896), 27 October 2026. The [UVM 1.2 User Guide](https://www.accellera.org/images/downloads/standards/uvm/uvm_users_guide_1.2.pdf), chapter 5, supplies register-layer context. [E13](examples.md#e13--separate-interrupt-status-mask-and-clear-behavior) and [E14](examples.md#e14--check-read-side-effects-and-illegal-register-accesses) are public cases with special behavior.

**Proposed reusable rule:** Derive a field-level register table from the applicable specification. Combine ordinary reset/access checks with targeted checks for side effects, volatile fields, locks and hardware/software interactions. Every exclusion from a generic test needs a reason and a planned alternative or an explicit unresolved dependency.

**Use when:** A design exposes a register map through one or more software/debug/bus interfaces.

**Required inputs:** Address maps, field positions, access policy, reset values by reset type, legal access widths/strobes, side effects and initiator permissions. Register models, bus adapters and backdoor paths are required only by methods that use them; record whether they exist.

**Planning procedure:**

1. Record address, field, access, reset domain/value, side effect and source reference. Include defined reserved/unmapped behavior. An access label such as RW does not override a more specific field description.
2. Propose ordinary read/write/reset checks for suitable stable fields. UVM register sequences are an option if the environment supports them. Reset stimulus, model reset kind and sequence exclusions must be configured for the target; selecting a sequence name does not establish those details.
3. Add targeted cases for each applicable behavior: write-one-to-clear, read-to-clear or FIFO pop, self-clearing commands, locks, partial writes, address aliasing, hardware/software collisions and retained state. Do not assume collision priority or a reserved read value.
4. Use bus access to check the externally visible contract. Direct register observation may help localize errors if valid paths exist; it does not replace interface checks or prove side effects. Avoid destructive blanket writes to volatile or side-effect registers.
5. At system level, select address/access/permission checks through each permitted initiator. Reuse block-level evidence where justified; agree the scope instead of automatically repeating every bit test at SoC level.

**Evidence to request:** The reviewed register table, selected checks, justified exclusions, targeted special-case checks and results by relevant interface/reset type. Apply TB06 when selecting evidence; a separate covergroup for every field is not required.

**Limits:** A model and RTL generated from the same erroneous description may agree. Compare the description with the governing specification. Correct register storage does not prove the controlled feature works. Unknown timing, reset values or simultaneous-update priority remain linked open questions. The comment's SVA snippets are illustrative and are not validated templates in this package.

**For the engineer:** Confirm the minimum field information, acceptable exclusions, and the appropriate split between block-level and system-level checking.
