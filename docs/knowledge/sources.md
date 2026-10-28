# Sources and comparable systems

Initial snapshot checked on 27 October 2026; revision 2 sources added and checked on 28 October 2026. Source credibility establishes provenance; engineering curation must still establish correctness and applicability. Existing comparative-system research below retains its original snapshot date.

## Source families

| Source | Material selected | Intended use |
| --- | --- | --- |
| OpenHW CORE-V-VERIF | Planning guidance, simulation-plan template and RV32I plan | Traceability, checking methods, coverage and concrete instruction-plan examples |
| OpenHW CV32E40P and CORE-V MCU | Pinned integration, interrupt and clock-domain specifications | Boot permission, interrupt acknowledgement, system event routing and domain assignments in E15–E18 |
| Accellera | UVM 1.2 User Guide | Environment, stimulus, monitor and scoreboard roles; adapt to the target UVM version |
| PULP | AXI verification-component, crossbar and mailbox documentation | Traffic, reference modeling and integration constraints; address/error/ordering and register-side-effect cases in E10–E14 |
| OpenTitan | Specifications, authored testplans and environment documents across six blocks | Peripheral tests, resets, errors, interrupts and cross-component handoff |
| RISC-V International | [Unprivileged ISA manual](https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf), ADDI section | Authoritative cross-check for K04; select the actual target ISA revision |
| Engineering contribution | [5a1aah's four comments on PR #4](https://github.com/noobjam/Project-x/pull/4#issuecomment-6454839896), 27 October 2026 | Proposed K13–K15 and corrections to uncertainty, coverage and example breadth; revised wording remains unapproved |

The rows below inventory the public files inspected or collected locally during preparation. They are linked upstream instead of vendored into this repository. Collection does not mean every passage has been reviewed or converted to an entry. The excerpts used for entries are visible in [patterns](patterns.md) and [examples](examples.md).

### openhw

**Version:** 1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3

- [docs/VerifPlans/VerificationPlanning101.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/VerificationPlanning101.md) — SHA-256 `14f149d0caecd2d305e4b23fdbb49ca8659955491adcc22ae43db116876f97ec`
- [docs/VerifPlans/README.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/README.md) — SHA-256 `ed2bd99760be5d7d7cb16d872d08384f2724f1d01a941186d49827e1e8773e7c`
- [LICENSE.md](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/LICENSE.md) — SHA-256 `3c95a5b32834e1c3b9006bceaef445e3f3c4153c4977957cc43213901159e572`
- [docs/VerifPlans/templates/CORE-V_Simulation_VerifPlan_Template.xlsx](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/templates/CORE-V_Simulation_VerifPlan_Template.xlsx) — SHA-256 `768bd0b789f0221ad5fa0fd46ebf8e52ffb38253b1f63368bc969c18ca61a19b`
- [docs/VerifPlans/ISA/RV32/Simulation/RV32I_Base_Instructions.xlsx](https://github.com/openhwfoundation/core-v-verif/blob/1dfa4836868fc2fc8e3754ee5c1c43fb42948aa3/docs/VerifPlans/ISA/RV32/Simulation/RV32I_Base_Instructions.xlsx) — SHA-256 `35a99d9080e6235fa1d626c217345b2c3fecf8c92aaaa10dccd127e724376815`

### accellera

**Version:** UVM 1.2 User Guide, October 8 2015

- [uvm_users_guide_1.2.pdf](https://www.accellera.org/images/downloads/standards/uvm/uvm_users_guide_1.2.pdf) — SHA-256 `6cddf735c3f7f700ef5f62b2954a28f7fb7e590a149314cbe5b0d342f99d131c`

### pulp

**Version:** 70b8e54fd460e3308e58be596ceb3566a6e3576e

- [README.md](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/README.md) — SHA-256 `9a8390200dee89eb56763f485145da896ac02c6c06eb12fdf7fbc2bbdca2eeb4`
- [LICENSE](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/LICENSE) — SHA-256 `6527a46225891b976fa94f634f6ee0cd22e1c7129d6f11c5c98c997627625fc7`

Revision 2 adds the following inspected documentation at the same pinned version. E10–E14 distinguish paraphrased source facts from our proposed tests; no upstream test pass is inferred.

- [doc/axi_xbar.md](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_xbar.md) — SHA-256 `7ded1f2ea27d5d3fd28b10fb1566a965c7e746966258077d422ebf51fe004a57`
- [doc/axi_lite_mailbox.md](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_lite_mailbox.md) — SHA-256 `64503e9e264162812590ad943c682859b92f9dd1a812259efa6b5f57896f3cc1`

### openhw-cv32e40p

**Version:** b353438ff469c030c89f6804f3b24a2852880e8b, pinned for revision 2 examples E15 and E17. These documents describe a particular core configuration and revision; do not treat them as universal RISC-V behavior.

- [docs/source/integration.rst](https://github.com/openhwgroup/cv32e40p/blob/b353438ff469c030c89f6804f3b24a2852880e8b/docs/source/integration.rst) — SHA-256 `0de3f22eff73fb2b9effecc675506d0c6b80b72d14cd031d51e65fc89d20cb7b`
- [docs/source/exceptions_interrupts.rst](https://github.com/openhwgroup/cv32e40p/blob/b353438ff469c030c89f6804f3b24a2852880e8b/docs/source/exceptions_interrupts.rst) — SHA-256 `8b7ecffb4bb6ddc429de5eef219288d6f46c1e07b640f0e6131b45fd55c53227`

### openhw-core-v-mcu

**Version:** 61fe7db2ebd13621975d97d484ef8fe99d3615a6, pinned for revision 2 examples E16 and E18. The MCU documents refer to a core-specific manual version. No compatibility with the independently pinned CV32E40P revision above is assumed. The selected text supplies architecture and maps, not every register, endpoint or timing definition needed to execute a test.

- [docs/doc-src/interrupts.rst](https://github.com/openhwgroup/core-v-mcu/blob/61fe7db2ebd13621975d97d484ef8fe99d3615a6/docs/doc-src/interrupts.rst) — SHA-256 `ac0c29efcc36b44cc1e3f68e14a41507efd8c8e6cd19838d2fd6fd7fdd8a9dbe`
- [docs/doc-src/clock_domains.rst](https://github.com/openhwgroup/core-v-mcu/blob/61fe7db2ebd13621975d97d484ef8fe99d3615a6/docs/doc-src/clock_domains.rst) — SHA-256 `6dcd04d4696d47a0c601db56e60a65bbc4b2cbfc943645b388b97857a607e78c`

### opentitan

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06

- [doc/contributing/dv/methodology/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/doc/contributing/dv/methodology/README.md) — SHA-256 `7ead652752048f617f445a987d808c354c4595c7044a7fd11e2537b77e0a2358`
- [hw/dv/sv/cip_lib/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/dv/sv/cip_lib/README.md) — SHA-256 `00b6fd758e725ebbcab51ffe885a7f6165def3e7f57409c3422d83a6e04a7d07`
- [hw/ip/uart/data/uart_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart_testplan.hjson) — SHA-256 `0c1288ba944faf969aafa8a03f63e4b67e421ecbc28b03870bf1de766e55fcd0`
- [hw/ip/uart/dv/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/dv/README.md) — SHA-256 `a4ea1b4e9dd33bc75590cae9185a4fa7504f6943eeef8e3a92eb68b6991b24ba`
- [hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md) — SHA-256 `6f9e15b9af2a77c41ee77717c87287a14635c84f6b3e6f2a7bec708628d77ba6`
- [hw/ip/i2c/data/i2c_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/i2c/data/i2c_testplan.hjson) — SHA-256 `7c7f8e85c34989c2720213e6135fc27a242d4538ce4e23c20a24a14c464da0cf`
- [hw/ip/i2c/dv/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/i2c/dv/README.md) — SHA-256 `d4fc081c242739e95b5307a3e1c59e218f1c5b96dcf128a530eabf83fe18d182`
- [hw/ip/i2c/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/i2c/doc/theory_of_operation.md) — SHA-256 `2fcd965f90e3b57153e27d64ea7d10cc8cd0a972b8375aafd912208641d0e97b`
- [hw/ip/spi_host/data/spi_host_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/spi_host/data/spi_host_testplan.hjson) — SHA-256 `b929968068dc6e11672e41ba09a836e5b8dd433a473edaf47f0a8e1227347aaf`
- [hw/ip/spi_host/dv/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/spi_host/dv/README.md) — SHA-256 `8b57dcfc8f03d25c6ac7f71d31a701be1457a179d33c5f7d4f173990465ff543`
- [hw/ip/spi_host/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/spi_host/doc/theory_of_operation.md) — SHA-256 `b33f4ca68279ffb39f02447647b1c134787dd503cc0ee3bfec12b5bac24a8904`
- [hw/ip/usbdev/data/usbdev_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/data/usbdev_testplan.hjson) — SHA-256 `8612a41be254d05e2c14a870b5e2f9c395aabce8cd0838283a7f8d0ac715c7a6`
- [hw/ip/usbdev/dv/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/dv/README.md) — SHA-256 `430142bed753d3e2682fefe9322ec40b2ea0657d4489495be37d94b4dbd8e6b4`
- [hw/ip/usbdev/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/doc/theory_of_operation.md) — SHA-256 `aa2521869452ae52a65bbb92105e1a21a8527ec0cf1538da94739b9af1868cd2`
- [hw/top_earlgrey/ip_autogen/gpio/data/gpio_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/gpio/data/gpio_testplan.hjson) — SHA-256 `0e4002d4b2cec098c0e0886faf07c24dafc18d69888a4b1559e2c6f9b7acce9a`
- [hw/top_earlgrey/ip_autogen/gpio/dv/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/gpio/dv/README.md) — SHA-256 `03ffefedbf1828ffebd55306a97ae1f96f0c1f47665561650f0a66ce16fa528c`
- [hw/top_earlgrey/ip_autogen/gpio/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/gpio/doc/theory_of_operation.md) — SHA-256 `e2a5ac0da9a98545c9242a70a27af4bf8c8cc75055f21de1e8d201d611577623`
- [hw/top_earlgrey/ip_autogen/pwrmgr/data/pwrmgr_testplan.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/pwrmgr/data/pwrmgr_testplan.hjson) — SHA-256 `2c50c34be60a9dcffbecc93ed62000c6572f2f5d4e9a541901be250254883d50`
- [hw/top_earlgrey/ip_autogen/pwrmgr/dv/README.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/pwrmgr/dv/README.md) — SHA-256 `80a4ffb3d0f4529f1eb60e652979a8cdc8e72f9016010886c495d3b73002d8ef`
- [hw/top_earlgrey/ip_autogen/pwrmgr/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/top_earlgrey/ip_autogen/pwrmgr/doc/theory_of_operation.md) — SHA-256 `c7bd5d37155391871ce88c72b1b9f7977d007a4c3e3119353d90db965fc1329c`

## What comparable systems actually use

Reported data usage is separate from what we can obtain and safely treat as curated knowledge.

### [Spec2Plan](https://63dac.conference-program.com/presentation/?id=WIP3284&sess=sess307)

**Reported source usage:** The published abstract describes specification-driven planning, testing-technique injection and evaluation on six OpenTitan blocks.

**Availability and limits:** Public abstract; it does not establish a downloadable production knowledge base.

**Relevance:** Use structured verification techniques and compare against expert plans. The reported benchmark is not proof of generalization.

### [Intel formal testplanning](https://dvcon-proceedings.org/wp-content/uploads/2B3-DVCon_India_2024_Final_Paper_1423.pdf)

**Reported source usage:** Experiments use OpenTitan's write packer and PULP designs including an ID queue and AXI-Lite crossbar; humans implement checkers from proposed plans.

**Availability and limits:** Published worked examples plus public design repositories; no universal approved plan corpus is established.

**Relevance:** Include multiple design families and check whether proposed tests can become useful checkers.

### [HAVEN](https://github.com/mcc311/haven)

**Reported source usage:** Its repository lists 16 OpenCores and Ultra-Embedded designs, specifications, DPI-C reference models, protocol templates and EDA-tool feedback.

**Availability and limits:** Public repository and benchmark; benchmark inclusion does not by itself establish engineering approval of every specification or model.

**Relevance:** Candidate sources for examples and environment structure. Its executable-testbench scope extends beyond our planning agent.

### [NVIDIA ChipNeMo](https://arxiv.org/html/2311.00176v2)

**Reported source usage:** An engineering assistant retrieves internal design/verification specifications, testbench regression and build documentation. Designers authored evaluation questions, answers and supporting passages.

**Availability and limits:** The paper is public; NVIDIA's internal corpus is not a downloadable dataset for us.

**Relevance:** Include project-specific engineering documentation and engineer-authored answers, not only generic public guidance.

### [STELLAR](https://arxiv.org/html/2601.19903v1)

**Reported source usage:** Retrieves structurally similar RTL/assertion pairs from the VERT dataset after filtering syntax errors.

**Availability and limits:** Published method using a named dataset. Syntax filtering alone does not certify functional correctness.

**Relevance:** Useful later for assertion examples; low priority for today's specification-to-plan knowledge base.

## Curation findings already identified

- **K04:** the OpenHW introductory ADDI example and its actual RV32I plan disagree about overflow. Check the applicable ISA before reusing the example.
- **K12:** pinned OpenTitan UART testplan wording disagrees with its specification on watermark clearing and FIFO depth. Preserve the boundary-testing method and resolve the detailed behavior.
- **E14:** the PULP mailbox register overview gives ERROR a zero default, while the Read Error field's detailed reset value is one. The expected reset value remains unresolved. This discrepancy does not prevent planning the separately documented read-to-clear and access-error checks.
- **Cross-project transfer:** OpenTitan UART and PULP mailbox threshold/status rules differ. Reuse the boundary/masking method while deriving the comparison and persistence rules from the target specification. CORE-V MCU event routing and CV32E40P interrupt pins describe different integration layers and independently pinned versions.

These are reasons to review individual entries instead of treating a repository's reputation as automatic approval.

## Attribution and reuse

Original source excerpts are identified beside their upstream links, versions and locations. Proposed rules, examples and checklist synthesis are Project X drafts. Third-party excerpts retain their authors' rights:

- Original CORE-V-VERIF material: Copyright OpenHW Group; Apache-2.0 WITH SHL-2.0. See [Solderpad 2.0](licenses/OpenHW-SHL-2.0.txt) and [Apache 2.0](licenses/Apache-2.0.txt).
- The newly linked CV32E40P/CORE-V MCU documents identify Apache-2.0 WITH [SHL-2.1](https://solderpad.org/licenses/SHL-2.1/); CV32E40P integration documentation credits OpenHW Group and Dolphin Design. Revision 2 links the originals and supplies attributed paraphrases and proposed checks, without vendoring these files. The older CORE-V-VERIF notices above remain unchanged.
- OpenTitan material: Copyright lowRISC contributors; [Apache 2.0](licenses/Apache-2.0.txt).
- PULP material: upstream [Solderpad 0.51 license](licenses/PULP-SHL-0.51.txt); source documentation is linked and quoted with attribution.
- The linked Accellera UVM 1.2 guide identifies Apache 2.0 licensing in its copyright page. The PDF is not republished here.
- Papers and the RISC-V manual are linked with limited summaries or quotations; no private research corpus is represented as downloadable.
- Engineering proposals remain attributed to GitHub contributor 5a1aah and linked to their original comments. Project X's edited rules are proposed adaptations, not claims of independent literature validation or final approval by that contributor.
