# Per-cycle bitplane costs

This investigation separates work inside the per-cycle bitplane path before
choosing another optimisation. It follows the rejected local changes in
[the preceding comparison](BITPLANE-SPANS.md).

## Diagnostic results

The private diagnostic samples approximately one in 64 `update_fetch` calls
after guest frame 3,000, then times their nested per-cycle operations. Compiler
memory barriers surround timer reads. A separate empty scope measures the timer
floor. This runs on the physical Cortex-A9 with Paula audio.

| Scope | Samples | Estimated seconds | Mean timer ticks per sample |
|---|---:|---:|---:|
| Entire per-cycle function | 761,360 | 27.416 | 187.55 |
| Event prefix | 761,360 | 3.312 | 22.66 |
| Fetch dispatch | 761,360 | 8.788 | 60.12 |
| Output suffix including flushing | 761,360 | 5.555 | 38.00 |
| Nested ChipRAM load/store body | 154,078 | 2.893 | 97.80 |
| Empty timer scope | 761,360 | 0.877 | 6.00 |

The event prefix includes stop handling and mode checks; a terminating fetch may
also drain output there. Fetch dispatch includes the nested memory body, pointer
updates and modulo handling. The output suffix includes state/counter updates
and conditional shifting/flushing.

**These are overlapping, instrumented estimates, not additive production costs.**
Nested timing and recording add overhead to enclosing scopes. Do not subtract
the empty scope from every row and claim an exact corrected timing, or compare
these totals directly with differently instrumented builds.

The memory-body mean is substantially above the timer floor. However, only
154,078 of 761,360 sampled cycles reach that body. Other cycles can be idle,
have DMA disabled or select inactive planes; this ratio is not an idle-cycle
percentage. The evidence supports investigating dispatch/state overhead rather
than treating raw ChipRAM reads as the only bottleneck.

The 6,000-frame diagnostic completed at 35.86 emulated FPS, which is not a
candidate speed result. CPU dispatches, guest cycles, final PC and framebuffer
matched the reference. All 3,330,048 PCM sample frames completed with device
error zero; 2,125 late-submit gaps remain. Core1 restoration and release passed.

## Candidate: an explicit idle-slot bound

Before the existing fixed-plane dispatch switches, test
`cycle_start < fm_maxplane`. Slots outside that bound cannot select a plane.
The switches and their constant plane arguments remain intact for active slots.
No cycle is skipped: event checks, counters, mode changes, output flushing and
the existing active fetch body still run in their original order.

This differs from earlier idle-cycle batching and table-driven dispatch. It
neither combines cycles nor introduces variable-plane addressing or a shared
out-of-line fetch helper.

- 940,032 sanitized native source-block comparisons match, including idle slots,
  disabled DMA, stop states and reserved plane counts.
- Four ARM memory/IRQ/beam/colour-write fixtures match CPU state, RAM and pixels.
- PAL/NTSC mixed-mode fixtures match across resolution, scroll and fetch changes.
- A separate audio fixture matches nonempty PCM hashes.

The per-cycle ARM functions change from 6,980/6,756/7,436 bytes to
6,988/6,764/7,440 bytes. Correct output and small code changes are not themselves
performance evidence.

## Matched hardware comparison

Both uninstrumented players run the same 6,000-frame Banshee script, with A1200
interpreter, PAL fullscreen and Paula audio. External gameplay input is suppressed
in private test hosts only. The installed controls remain unchanged.

| Build | Elapsed seconds | Whole-run emulated FPS | Audio late-submit gaps |
|---|---:|---:|---:|
| Fresh current reference | 162.445 | 36.936 | 2,063 |
| Explicit idle-slot bound | 163.206 | 36.763 | 2,067 |

The candidate is **0.47% slower** in this pair. This is not evidence for a
universal regression or its exact cause, but there is no positive reason to
promote it. Audio gaps remain essentially unchanged.

Both match 116,472,634 CPU dispatches, 814,003,022 guest cycles, PC `00029056`
and framebuffer SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
All 3,330,048 PCM sample frames complete with device error zero. Register/MMU/
cache-witness restoration and owned-memory release pass. Delivery completion
does not establish audible quality.

## Outcome

Three physical runs cover 18,000 guest frames. The temporary players were removed
and installed normal/FPU hashes verified unchanged; Core1 is free. No product
version, release or firmware change is warranted.

The measurements distinguish memory work from dispatch and output handling,
but the local guard fails the end-to-end performance gate. Further investigation
should examine repeated state loads and call boundaries across whole fetch-loop
iterations, with mid-line mode changes and DMA/output boundaries preserved.
That is a new investigation, not a measured speedup or an implemented change.

[Source patches, fixtures, build hashes and physical logs](cycle-costs/).
Build scripts require the prepared workspace; no ROM or game media is included.
