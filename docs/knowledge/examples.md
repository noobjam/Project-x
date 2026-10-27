# Worked public-source examples

All entries are **proposed and unreviewed**. Original evidence and our proposed adaptations are identified separately. Use the [review template](REVIEW_TEMPLATE.md) to keep, correct or remove entries and state applicability.

These five examples are proposed adaptations of the pinned OpenTitan specifications. They have not been executed. IDs match the local curation pack; gaps in the sequence are intentional. [K12](patterns.md#k12--resolve-specificationtestplan-disagreements-before-reuse) records disagreements in the related authored UART testplan.

## E01 — Reset a nonempty UART receive buffer

**Reusable lesson:** Check reset with meaningful nonempty state.

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
