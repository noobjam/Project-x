# Worked public-source examples

All entries are **proposed and unreviewed**. Original evidence and our proposed adaptations are identified separately. Use the [review template](REVIEW_TEMPLATE.md) to keep, correct or remove entries and state applicability.

These 14 examples are proposed adaptations of pinned specifications from **OpenTitan, PULP AXI, OpenHW CV32E40P and OpenHW CORE-V MCU**. They have not been executed or engineering-approved. E10–E18 were added after the [request for broader, transferable examples](https://github.com/noobjam/Project-x/pull/4#issuecomment-6455401309). E04–E07 remain private and are intentionally absent. The original local v1 pack is a historical snapshot; this GitHub edition contains the revision 2 additions.

## Find a behavior, then check applicability

| Behavior | Cases | Transfer question |
| --- | --- | --- |
| Reset with state; permission to start | E01, E15 | What resets, what survives, and what separately permits operation? |
| Thresholds and overflow | E02, E03, E13 | Does the boundary include equality; is the notification sticky or level-based? |
| Request/acknowledgement and ownership | E08, E09, E17 | What observation proves acceptance or completion, and when is it valid? |
| Address routing, overlap and unmapped accesses | E10, E11 | Which target wins, and does an unmatched address cause an error or a default route? |
| Concurrent requests and backpressure | E12 | Which ordering relationships must hold, and what may stall? |
| Register policies and side effects | E13, E14 | What does reading/writing actually do, beyond the access label? |
| Interrupt mapping through the subsystem | E16, E17 | Which stage translates the event, masks it and acknowledges it? |
| Clock-domain connections | E18 | Which source feeds each destination, under which documented mode? |

For each case, use the **reusable lesson** to recognize a candidate pattern, then re-derive its values and expectations from the new design's specification. A matching block name is insufficient. The proposed tests below are our adaptations, not tests claimed to exist or pass upstream. Source summaries are paraphrases; existing original excerpts remain marked separately. [Sources](sources.md) pins versions and hashes.

Useful counterexamples: E02's OpenTitan watermark includes equality; the PULP mailbox threshold discussed in E13 is strictly above its threshold. E08's activation can be delayed; E17's interrupt ID is meaningful during an acknowledgement pulse. Those details must not be flattened into one universal rule. [K12](patterns.md#k12--resolve-specificationtestplan-disagreements-before-reuse) and E14 preserve source disagreements.

## E01 — Reset a nonempty UART receive buffer

**Reusable lesson:** Check reset with meaningful nonempty state.

**Transfer to another design:** Apply to a queue, DMA descriptor buffer or pending work only when its reset semantics are specified. Re-derive whether data is discarded, retained or drained; a UART FIFO reset does not define a system warm reset.

**Why it matters:** This avoids a plausible plan that misses the distinguishing condition or invents an unsupported outcome.

**Use when:** Use the pattern only when the new specification defines an equivalent behavior.

**Limits:** Names, capacities, bit fields, timing and allowed exceptions belong to this example's source and must be re-derived for a new design.

**Starting conditions in this example:** Use the pinned UART configuration and establish that the RX FIFO contains accepted data.

**Action:** Write 1 to FIFO_CTRL.RXRST; read back the RXRST field.

**Proposed expected result:** The RX FIFO is reset and RXRST reads as zero. Do not infer a numeric RDATA value when the FIFO is empty.

**Observation / implementation gaps:** Engineer to identify the supported empty/occupancy observation and completion timing from the register specification or testbench.

**Source:** [OpenTitan — hw/ip/uart/data/uart.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart.hjson#L332-L337)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 332–337.

<details>
<summary>Read the original source excerpt</summary>

````text
        { bits: "0",
          swaccess: "wo",
          hwaccess: "hro",
          name: "RXRST",
          desc: "RX fifo reset. Write 1 to the register resets RX_FIFO. Read returns 0"
        }
````

</details>

**For the engineer:** Is this a useful reset check? What observation, timing and occupancy variations are needed?

## E02 — Check UART watermark at the threshold

**Reusable lesson:** Include the exact boundary, not just values far above or below it.

**Transfer to another design:** Identify the comparison operator, legal threshold range and notification behavior first. The PULP mailbox in E13 uses a strict threshold and sticky status; do not copy this UART's equality or clearing rules into it.

**Why it matters:** This avoids a plausible plan that misses the distinguishing condition or invents an unsupported outcome.

**Use when:** Use the pattern only when the new specification defines an equivalent behavior.

**Limits:** Names, capacities, bit fields, timing and allowed exceptions belong to this example's source and must be re-derived for a new design.

**Starting conditions in this example:** Select a documented RXILVL threshold T and isolate the RX watermark status from unrelated interrupts.

**Action:** Reach occupancies T-1, T and T+1; attempt to clear status while occupancy remains at least T; then drain below T.

**Proposed expected result:** The watermark condition includes equality, remains active while occupancy is at least T and cannot be removed by a status write while that condition holds.

**Observation / implementation gaps:** Observe the watermark condition/status. Any external interrupt-pin check must additionally configure and verify the documented enables.

**Source:** [OpenTitan — hw/ip/uart/data/uart.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart.hjson#L344-L378)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 344–378.

<details>
<summary>Read the original source excerpt</summary>

````text
        { bits: "4:2",
          name: "RXILVL",
          desc: '''Trigger level for RX interrupts. If the FIFO depth is greater than or equal to
                the setting, it raises rx_watermark interrupt.
                ''',
          enum: [
            { value: "0",
              name: "rxlvl1",
              desc: "1 character"
            },
            { value: "1",
              name: "rxlvl2",
              desc: "2 characters"
            },
            { value: "2",
              name: "rxlvl4",
              desc: "4 characters"
            },
            { value: "3",
              name: "rxlvl8",
              desc: "8 characters"
            },
            { value: "4",
              name: "rxlvl16",
              desc: "16 characters"
            },
            { value: "5",
              name: "rxlvl32",
              desc: "32 characters"
            },
            { value: "6",
              name: "rxlvl62",
              desc: "62 characters"
            },
          ]
````

</details>

**Source:** [OpenTitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L136-L136)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 136–136.

<details>
<summary>Read the original source excerpt</summary>

````text
If the RX FIFO level becomes greater than or equal to RX water mark level (configurable via [`FIFO_CTRL.RXILVL`](registers.md#fifo_ctrl--rxilvl)), the `rx_watermark` interrupt is raised to inform SW.
````

</details>

**Source:** [OpenTitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L138-L139)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 138–139.

<details>
<summary>Read the original source excerpt</summary>

````text
Note that the watermark interrupts and the empty interrupt are level-based status interrupts.
They will stay asserted for as long as the FIFO levels are in violation of the configured level and cannot be cleared by writing to the status register.
````

</details>

**For the engineer:** Confirm timing, status semantics and useful threshold selections. What defect would this test distinguish?

## E03 — Overflow a full UART receive buffer

**Reusable lesson:** Separate accepted data from data intentionally discarded on overflow.

**Transfer to another design:** First establish whether a full destination drops input, rejects it, overwrites old data or applies backpressure. This example fits the documented drop-new-input case; it is unsuitable as the expectation for a lossless stalled interface.

**Why it matters:** This avoids a plausible plan that misses the distinguishing condition or invents an unsupported outcome.

**Use when:** Use the pattern only when the new specification defines an equivalent behavior.

**Limits:** Names, capacities, bit fields, timing and allowed exceptions belong to this example's source and must be re-derived for a new design.

**Starting conditions in this example:** Fill the pinned 64-byte RX FIFO with a known sequence of valid characters; prevent software from draining it.

**Action:** Receive one more valid character, check overflow status, then drain accepted data.

**Proposed expected result:** The extra character is dropped and rx_overflow is asserted. The extra character must not appear among the accepted receive data.

**Observation / implementation gaps:** Use the documented interrupt/status path and RDATA accesses; avoid checking a fixed value after the FIFO becomes empty.

**Source:** [OpenTitan — hw/ip/uart/data/uart.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart.hjson#L171-L176)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 171–176.

<details>
<summary>Read the original source excerpt</summary>

````text
    { name:    "RxFifoDepth",
      desc:    "Number of bytes in the RX FIFO.",
      type:    "int",
      default: "64",
      local:   "true",
    }
````

</details>

**Source:** [OpenTitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L63-L63)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 63–63.

<details>
<summary>Read the original source excerpt</summary>

````text
If the STOP bit is detected as high and the optional parity bit is correct the data byte is pushed into a 64-byte RX FIFO.
````

</details>

**Source:** [OpenTitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L147-L147)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 147–147.

<details>
<summary>Read the original source excerpt</summary>

````text
#### rx_overflow
````

</details>

**Source:** [OpenTitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L149-L149)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 149–149.

<details>
<summary>Read the original source excerpt</summary>

````text
If RX FIFO receives an additional write request when its FIFO is full, the interrupt `rx_overflow` is asserted and the character is dropped.
````

</details>

**Source:** [OpenTitan — hw/ip/uart/doc/theory_of_operation.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/doc/theory_of_operation.md#L64-L64)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 64–64.

<details>
<summary>Read the original source excerpt</summary>

````text
The data can be read out by reading the [`RDATA`](registers.md#rdata) register.
````

</details>

**Source:** [OpenTitan — hw/ip/uart/data/uart.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/uart/data/uart.hjson#L303-L314)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 303–314.

<details>
<summary>Read the original source excerpt</summary>

````text
    { name: "RDATA",
      desc: "UART read data",
      swaccess: "ro",
      hwaccess: "hrw",
      hwext: "true",
      hwre: "true",
      fields: [
        { bits: "7:0" }
      ]
      tags: [// read wdata when fifo is empty, dut may return unknown data
             "excl:CsrAllTests:CsrExclCheck"]
    }
````

</details>

**For the engineer:** Confirm full/empty observations, overflow clearing and whether existing data preservation needs an additional explicit requirement.

## E08 — Wait for USB wake-module activation

**Reusable lesson:** Separate a request from acknowledgement of an ownership change.

**Transfer to another design:** Look for a documented request/completion contract in power, reset, DMA or resource handoff. Identify the completion observation and ownership transition; an ordinary register write with immediate effect needs a different check.

**Why it matters:** This avoids a plausible plan that misses the distinguishing condition or invents an unsupported outcome.

**Use when:** Use the pattern only when the new specification defines an equivalent behavior.

**Limits:** Names, capacities, bit fields, timing and allowed exceptions belong to this example's source and must be re-derived for a new design.

**Starting conditions in this example:** Satisfy the sleep-entry prerequisites in the complete supplied handoff procedure.

**Action:** Write SUSPEND_REQ; observe MODULE_ACTIVE before relying on the AON module's monitoring and pullup ownership.

**Proposed expected result:** Activation may be delayed. The plan must not assume that the request write completes the handoff immediately.

**Observation / implementation gaps:** Observe MODULE_ACTIVE and the available ownership/monitoring checks. An engineering-approved timeout is needed for an executable test; no cycle bound is supplied here.

**Source:** [OpenTitan — hw/ip/usbdev/doc/wake_resume.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/doc/wake_resume.md#L26-L29)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 26–29.

<details>
<summary>Read the original source excerpt</summary>

````text
2. Software hands control to the AON module.
   - Software writes a `1` to [`wake_control.suspend_req`](registers.md#wake_control).
   - The AON module transitions to the active state and takes over the pullup enable.
     It begins monitoring for events that trigger waking / resuming / resetting.
````

</details>

**Source:** [OpenTitan — hw/ip/usbdev/data/usbdev.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/data/usbdev.hjson#L1225-L1238)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 1225–1238.

<details>
<summary>Read the original source excerpt</summary>

````text
    { name: "wake_control",
      desc: "USB wake module control for suspend / resume",
      swaccess: "wo",
      hwaccess: "hro",
      hwext: "true",
      hwqe: "true",
      async: "clk_aon_i",
      fields: [
        {
          bits: "0",
          resval: "0",
          name: "suspend_req",
          desc: '''
                Suspend request to the wake detection module.
````

</details>

**Source:** [OpenTitan — hw/ip/usbdev/data/usbdev.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/data/usbdev.hjson#L1240-L1243)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 1240–1243.

<details>
<summary>Read the original source excerpt</summary>

````text
                Trigger the wake detection module to begin monitoring for wake-from-suspend events.
                When written with a 1, the wake detection module will activate.
                Activation may not happen immediately, and its status can be verified by checking wake_events.module_active.
                '''
````

</details>

**For the engineer:** What observation proves ownership, and how should the test handle a request coinciding with resume?

## E09 — Check USB wake acknowledgement completion

**Reusable lesson:** Observe asynchronous completion and consider events around handoff.

**Transfer to another design:** Derive where events are retained during the transition and which action releases ownership. Do not assume another protocol uses this USB block's capture path or completion status.

**Why it matters:** This avoids a plausible plan that misses the distinguishing condition or invents an unsupported outcome.

**Use when:** Use the pattern only when the new specification defines an equivalent behavior.

**Limits:** Names, capacities, bit fields, timing and allowed exceptions belong to this example's source and must be re-derived for a new design.

**Starting conditions in this example:** Reach the documented wake-acknowledgement point with the AON module active and the main USB block restored as required.

**Action:** Issue WAKE_ACK and observe completion through MODULE_ACTIVE plus relevant pullup/event observations.

**Proposed expected result:** The AON module releases pullup control, clears stored events and returns inactive. Completion may be asynchronous; do not assume immediate completion.

**Observation / implementation gaps:** Engineer to specify observable signals/status and timing. Events arriving around acknowledgement need separate treatment using the documented capture path.

**Source:** [OpenTitan — hw/ip/usbdev/doc/wake_resume.md](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/doc/wake_resume.md#L53-L57)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 53–57.

<details>
<summary>Read the original source excerpt</summary>

````text
6. Software issues [`wake_control.wake_ack`](registers.md#wake_control) to the AON module.
   - The AON module stops monitoring events and controlling the pull-ups, restoring control to the full-power `usbdev` module.
   - The AON module also clears the stored events.
     Events that occurred between reading the stored values in the AON module and acknowledging the wake-up are captured in the `usbdev_linkstate` module.
7. If software determined the state transition should be back to an active state, software issues [`usbctrl.resume_link_active`](registers.md#usbctrl).
````

</details>

**Source:** [OpenTitan — hw/ip/usbdev/data/usbdev.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/data/usbdev.hjson#L1247-L1252)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 1247–1252.

<details>
<summary>Read the original source excerpt</summary>

````text
        {
          bits: "1",
          resval: "0",
          name: "wake_ack",
          desc: '''
                Wake acknowledgement.
````

</details>

**Source:** [OpenTitan — hw/ip/usbdev/data/usbdev.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/data/usbdev.hjson#L1254-L1256)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 1254–1256.

<details>
<summary>Read the original source excerpt</summary>

````text
                Signal to the wake detection module that it may release control of the pull-ups back to the main block and return to an inactive state.
                The release back to normal state may not happen immediately.
                The status can be confirmed via wake_events.module_active.
````

</details>

**Source:** [OpenTitan — hw/ip/usbdev/data/usbdev.hjson](https://github.com/lowRISC/opentitan/blob/d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06/hw/ip/usbdev/data/usbdev.hjson#L1258-L1276)

**Version:** d55a81d1c21b8b35b11175ea5c4d3e06ef2a1d06. **Location:** lines 1258–1276.

<details>
<summary>Read the original source excerpt</summary>

````text
                Note that this bit can also be used without powering down, such as when usbdev detects resume signaling before transitions to low power states have begun.
                '''
        },
      ]
    }
    { name: "wake_events",
      desc: "USB wake module events and debug",
      swaccess: "ro",
      hwaccess: "hwo",
      async: "clk_aon_i",
      fields: [
        {
          bits: "0",
          resval: "0",
          name: "module_active",
          desc: '''
                USB aon wake module is active, monitoring events and controlling the pull-ups.
                '''
        }
````

</details>

**For the engineer:** Confirm prerequisites, completion checks and the required race scenarios before approving this example.

## E10 — Check address boundaries and overlapping decode rules

**Reusable lesson:** Turn range definitions and priority into routing checks at the exact boundaries. Related rule: K14; address decoding is functional behavior beyond simple wiring.

**Source fact (paraphrase):** PULP's crossbar includes each range's start and excludes its end. For overlapping ranges, the rule at the higher array position wins. Its map cannot change while any incoming AW or AR channel is valid. [Pinned address-map documentation](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_xbar.md#L18-L28).

**Proposed setup:** Use a controllable crossbar instance and observable target ports. The following is an **illustrative test configuration, not an address map from the user's design**: rule 0 maps `[0x1000, 0x2000)` to target A; rule 1 maps `[0x1800, 0x1900)` to target B. Hold the configuration stable and use aligned, single-beat, four-byte accesses.

| Proposed accesses | Expected destination in this configuration |
| --- | --- |
| `0x1000`, `0x17FC` | A |
| `0x1800`, `0x18FC` | B, because rule 1 wins the overlap |
| `0x1900`, `0x1FFC` | A |
| `0x0FFC`, `0x2000` | No rule matches; evaluate the configured fallback using E11 |

**Observation / evidence:** Exercise reads and writes; record the accepted request's address, selected target and returned response. Check that an access reaches only the selected destination. A parameterized test with a result per case is sufficient evidence for these cases; it need not create one covergroup per row.

**Transfer and limits:** Re-derive alignment, range convention, overlap priority and permitted transfers for the new interconnect. If overlap is forbidden, plan an illegal-configuration check instead. This case does not establish burst-boundary behavior, security permissions or arbitration fairness.

**For the engineer:** Are overlap and default routing legitimate configurations in your target? Which access sizes and initiators must the integration check cover?

## E11 — Distinguish an unmapped-address error from a default route

**Reusable lesson:** Missing a decode rule does not universally mean an error; configuration may define a fallback destination.

**Source fact (paraphrase):** PULP's crossbar uses an internal decode-error responder for an unmatched address unless a default destination is enabled for the incoming port. The error responder completes the transaction with the required beat count. Default-route changes have the map's quiescence restriction. [Pinned decode-error/default behavior](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_xbar.md#L31-L35).

**Proposed setup and action:** Choose an address outside every range and responsive test targets. With fallback disabled, issue a legal read and write and check the documented error response and completion. Drain traffic, change the configuration at a permitted idle point, enable a known default target, and repeat the address. Repeat for incoming ports with different fallback settings.

**Observation / evidence:** Record destination, response identity and beat completion. With fallback disabled, no normal target should receive the request. With fallback enabled, check forwarding to the selected target and its actual documented response; do not assume the target always returns success. Track timeouts separately from protocol errors.

**Transfer and limits:** Derive error encoding, error data, permitted bursts and fallback rules from the new specification. Do not reuse PULP's sentinel read data as a generic AXI expectation. A missing fallback definition becomes an open question on the affected check.

**For the engineer:** Confirm the supported error/default cases and the observation point that distinguishes a crossbar error from a target-generated error.

## E12 — Check ordering when two requests share an identity

**Reusable lesson:** Exercise a constrained relationship between outstanding requests, including intentional backpressure, rather than testing each destination in isolation.

**Source fact (paraphrase):** PULP stalls a second same-direction request to a different destination while an earlier request with the same compared ID remains outstanding. The configured number of low ID bits determines conflicts. [Pinned ordering and stalls](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_xbar.md#L81-L85).

**Proposed setup and action:** Use two responsive targets with controllable response delay. Configure the ID comparison width explicitly and an observation point whose buffering is understood. Send a read to A; hold A's response pending. Present a read with the same compared ID to B. Observe the documented stall, allow A to complete, then check B's completion. Repeat for writes using a legal address/data sequence. Add a different-ID control case to distinguish this rule from general resource exhaustion; do not require a fixed acceptance cycle.

**Observation / evidence:** Correlate accepted requests and responses by ID, direction and target. Record that the intended outstanding-request overlap occurred and the required order held. If external pipeline stages accept requests before the decoder, observe the relevant internal boundary or account for buffering explicitly.

**Transfer and limits:** Reordering buffers, ID remapping and queue depth change this test's expectations. A new design may legally accept both requests and reorder responses. Derive its actual contract; a stall is not inherently a bug. Liveness requires stated response/fairness assumptions and an agreed timeout, not an invented cycle bound.

**For the engineer:** Which ordering properties are required at the subsystem boundary, and what buffering/ID information will the agent receive?

## E13 — Separate interrupt status, mask and clear behavior

**Reusable lesson:** Event capture, notification enable and acknowledgement are distinct behaviors. Related rules: K14 and K15.

**Source fact (paraphrase):** PULP mailbox IRQS captures sticky events even when IRQEN masks notification. Writing one acknowledges the selected status bit; writing zero does not. IRQP combines status with enables. Its threshold events use a strict greater-than comparison. [Pinned IRQS/IRQEN/IRQP definitions](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_lite_mailbox.md#L115-L153).

**Proposed setup:** Configure a known mailbox width/depth and interrupt polarity/mode. Obtain register addresses from that configuration. Use one isolated error event, such as a read from an empty FIFO, then prevent new events. Observe registers through the bus; do not confuse the separate read-to-clear ERROR register with IRQS.

| Action | Proposed check |
| --- | --- |
| Generate the event with its notification disabled | Status records the event; its pending notification remains masked |
| Enable its notification | The retained status contributes to pending notification |
| Write zero to its IRQS bit | No acknowledgement/clear of that bit |
| Write one to that bit, with no new event | Status and the corresponding pending notification clear |

**Observation / evidence:** Record the event, register responses and interrupt output under the chosen trigger mode. Also inspect unaffected status bits. A readback-only test that never creates the event cannot establish correct capture.

**Transfer and limits:** Re-derive mask placement, status persistence, polarity and clearing behavior. E02's OpenTitan watermark is level-based and includes equality; these mailbox rules are different. Simultaneous hardware-set/software-clear priority is not established by this excerpt: leave that expected result unresolved until a governing source is supplied.

**For the engineer:** Confirm the masking/clearing cases and whether simultaneous-update priority is required in the initial plan.

## E14 — Check read side effects and illegal register accesses

**Reusable lesson:** A register's access label is insufficient to select safe generic tests; include read side effects and the bus response to prohibited access. Related rule: K15.

**Source fact (paraphrase):** PULP mailbox ERROR clears on read. Writes to read-only registers and reads from write-only registers return SLVERR. The register overview lists ERROR reset as zero, but the detailed Read Error bit lists reset one: **the source is internally inconsistent**. [Pinned register overview](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_lite_mailbox.md#L37-L53) and [ERROR definition](https://github.com/pulp-platform/axi/blob/70b8e54fd460e3308e58be596ceb3566a6e3576e/doc/axi_lite_mailbox.md#L82-L90).

**Proposed setup and action:** Isolate new error events. Read ERROR to clear existing state, induce a documented empty-mailbox read error, then read ERROR twice. Check the captured error on the first observation and clearing on the second with no intervening event. Separately attempt a write to read-only STATUS and a read from write-only MBOXW; check their specified error responses.

**Observation / evidence:** Record bus completions and returned values, with competing readers disabled. Keep these accesses out of a blanket bit-bash test. If a monitor, debugger or background sequence reads ERROR, it can consume the evidence before the intended check.

**Open question to keep in the output:** What is the authoritative reset value of ERROR.Read Error? Cite both conflicting tables and flag only the dependent reset expectation. The read-side-effect and access-error checks can still be planned. Do not resolve this conflict by adopting current RTL behavior.

**Transfer and limits:** Read-only does not universally mean reads have no side effects, nor do prohibited accesses universally return SLVERR. Re-derive access width, timing and policy. Error responses alone do not prove absence of all side effects; add such checks only against a defined contract.

**For the engineer:** Resolve the reset conflict and confirm the stimulus needed to isolate destructive reads in a system environment.

## E15 — Separate reset release from permission to boot

**Reusable lesson:** Releasing reset and permitting a block to start can be separate controls; test their sequence. Related rule: K13.

**Source fact (paraphrase):** CV32E40P holds off its first fetch while fetch_enable_i is low after reset. A high cycle outside reset enables fetching, after which that control is ignored. boot_addr_i determines the first program counter and must remain stable after enabling. [Pinned integration interface](https://github.com/openhwgroup/cv32e40p/blob/b353438ff469c030c89f6804f3b24a2852880e8b/docs/source/integration.rst#L147-L176).

**Proposed setup and action:** Provide a running clock, legal stable boot address, working instruction memory, and a short program that will not sleep or enter debug. Release reset while holding fetch enable low. Check that no initial fetch starts. Pulse enable for at least one clock cycle, then return it low. Observe execution starting at the boot address and continuing; the low control after startup must not be treated as a fresh halt request.

**Observation / evidence:** Use both the instruction interface and an architectural PC/retirement observation if available. A fetch bus can have alignment/prefetch behavior, so do not equate every bus address with the exact program counter. Identify missing observations as testbench dependencies.

**Transfer and limits:** Re-derive reset polarity, enable sampling and restart policy. This case is unsuitable for an enable that continuously gates operation. No fixed boot latency or behavior for changing the address after startup is inferred. Direct core-pin tests do not by themselves verify the SoC reset controller or the wiring of its boot controls.

**For the engineer:** Confirm observation points and which core-pin checks must also be exercised through the actual system reset/start controls.

## E16 — Trace an event through a two-level interrupt map

**Reusable lesson:** Verify the mapping at each integration stage instead of assuming a peripheral event index equals a CPU interrupt number. Related rule: K14.

**Source fact (paraphrase):** CORE-V MCU aggregates enabled platform events through a FIFO-based second level into CPU external interrupt 11. Software then reads event-generator information to identify the platform event. Its map assigns event ranges to UART, QSPI, GPIO and other sources. [Pinned interrupt strategy and maps](https://github.com/openhwgroup/core-v-mcu/blob/61fe7db2ebd13621975d97d484ef8fe99d3615a6/docs/doc-src/interrupts.rst#L23-L127).

**Proposed setup and action:** Select two documented event sources and obtain their exact trigger, enable and event-read/acknowledgement definitions from the relevant peripheral/event-controller documents. Enable the required stages. Trigger each source separately, confirm the external interrupt route, and check the reported event identity. Then trigger two distinguishable events in a controlled order and inspect retention/ordering using the defined queue contract.

**Observation / evidence:** Record source event, intermediate event identity, CPU interrupt and software-visible report. Check inactive destinations where appropriate. Boundary forcing can verify a map, while a real peripheral trigger also exercises upstream generation; record which was used.

**Open questions:** The coarse interrupt map alone does not define every source trigger, event-pop operation, queue capacity, overflow response or simultaneous-event priority. Attach those missing inputs to the dependent checks and retain an unresolved expectation where necessary. Do not invent an event-register address or acknowledgement sequence.

**Transfer and limits:** A direct vector, priority interrupt controller and event FIFO need different tests. CPU-pin level sensitivity does not determine whether upstream peripheral events are edge-captured. Do not combine this MCU revision with an arbitrary newer core revision without checking the actual integration version.

**For the engineer:** Which additional register/interface documents are necessary to turn this mapping example into an executable system test?

## E17 — Observe interrupt acknowledgement only when it is valid

**Reusable lesson:** Sample response identity in its valid window and test each enable layer independently. Related rules: K14 and K15.

**Source fact (paraphrase):** CV32E40P requires both global and per-interrupt enables. Its acknowledgement pulses for one cycle when an interrupt is taken; the interrupt ID is valid during that pulse. Source clearing depends on the connected hardware or software mechanism. [Pinned interrupt interface and enables](https://github.com/openhwgroup/cv32e40p/blob/b353438ff469c030c89f6804f3b24a2852880e8b/docs/source/exceptions_interrupts.rst#L48-L105).

**Proposed setup and action:** Run a simple program outside debug with valid handler setup and an observable interrupt interface. For one supported level-sensitive source, test global-disabled, source-disabled and both-enabled configurations. Establish each mask configuration before applying the event. In the enabled case, record acknowledgement width and the ID during acknowledgement; use the specified external clearing mechanism before allowing a retrigger.

**Observation / evidence:** Correlate the asserted source with acknowledgement and handler entry. Observe the ID only while valid. Record the actual mask settings and that the event reached the core. If the observation window needs a bound, obtain it from the environment/specification; an arbitrary short wait cannot prove the event will never be handled.

**Transfer and limits:** Different cores/controllers may use a persistent valid/ready response, a software claim register or another acknowledgement protocol. Do not copy the one-cycle pulse, source numbering or clearing mechanism. This check does not establish simultaneous-interrupt priority or nested-interrupt behavior.

**For the engineer:** Confirm the enable combinations and the evidence required to distinguish masking from an event that never reached the core.

## E18 — Account for clock domains without inventing timing

**Reusable lesson:** A clock architecture can support a connectivity plan before it supplies enough information for timing checks. Related rule: K13.

**Source fact (paraphrase):** CORE-V MCU describes separate SoC, peripheral and FPGA clock domains derived from a reference/PLL/divider structure. CPU and memory use the SoC domain; UDMA peripherals and eFPGA use their respective domains. [Pinned clock-domain document](https://github.com/openhwgroup/core-v-mcu/blob/61fe7db2ebd13621975d97d484ef8fe99d3615a6/docs/doc-src/clock_domains.rst#L20-L61).

**Proposed planning table:** These are architecture-level destinations, not invented RTL hierarchy paths.

| Destination group | Expected domain from this source | Information still required for a concrete check |
| --- | --- | --- |
| CPU and memory subsystem | SoC clock | Exact endpoints, gating/modes and allowed clock controls |
| UDMA peripheral clock generation | Peripheral clock | Source-to-generated-clock relationships and peripheral modes |
| eFPGA primary clock | FPGA clock | Endpoint inventory, mux/bypass controls and power context |

**Proposed action / evidence:** Reconcile the table with the integration endpoint inventory and record unmapped inputs. Plan a check of each specified source-to-destination relationship. With defined operating modes and divider settings, add appropriate frequency/ratio observations; distinguish clocks by source and mode as well as frequency. Record missing timing information against the affected checks.

**Transfer and limits:** The new design's domain assignments, frequencies and reset controls must come from its own architecture. This document alone is insufficient to assert glitch-free switching, PLL lock time, reset release ordering or CDC/RDC safety. No numerical timing limit or direct wire equality is inferred across a divider or gate.

**For the engineer:** What minimum clock-control and reset documentation should accompany an architecture diagram before these checks are considered implementable?
