# Bitplane spans and fetch dispatch

All three private candidates matched the reference output but did not improve
Banshee performance. None is enabled in the installed normal/FPU players.

## Profile

A private diagnostic sampled approximately one in 64 `update_fetch` calls after
guest frame 3,000, with Paula audio enabled. The 6,000-frame physical run matched
reference CPU dispatches, cycles, PC and framebuffer, then released Core1 cleanly.

| Timed path | Samples | Estimated seconds |
|---|---:|---:|
| Whole update_fetch | 14,870 | 22.720 |
| Preparation loop | 14,870 | 5.025 |
| Bulk do_long_fetch | 11,980 | 2.930 |
| Trailing per-cycle loop | 13,908 | 10.281 |
| Nested block setup | 25,674 | 0.841 |
| Nested final shifter drain | 12,062 | 2.333 |

Estimates scale sampled ticks by 64 and the calibrated hardware timer frequency.
They include instrumentation costs and overlap: block setup and final draining
can occur inside the other stages. **Do not add the rows.** The instrumented
35.16 emulated FPS is not an optimisation result.

Preparation and trailing work exceed bulk-fetch time in this profile. Existing
bulk fetching already handles much of the eligible work; earlier idle-cycle
batching did not improve performance. Timing boundaries remain necessary for
mid-line register writes, DMA stops, output flushing and resolution changes.

## First-round candidates

**Denise once:** block setup already calls `update_denise`, then calls a delay
helper that repeats it. The candidate keeps the first update and calls the
delay-calculation helper directly. It removes one source-level update per block.

**Outlined fetch:** share the AGA 64-bit fetch body through one non-inlined
function, preserving every fetch and its order. The generated per-cycle function
shrinks from 7,436 bytes to 2,184 bytes plus a 492-byte helper. The 16/32-bit paths
remain unchanged. No cache-hit or instruction-cache-miss improvement was measured.

Correctness gates:

- 200,000 sanitized native block-state/colour-event comparisons for Denise once.
- Four ARM memory/interrupt/beam/colour-write fixtures for both candidates.
- PAL and NTSC mixed-mode fixtures exercising all three block-setup functions,
  including mid-line resolution, scroll and fetch-mode changes.
- Matching CPU state, RAM, pixels and nonempty PCM hashes in the audio fixture.

## Physical comparison

All builds use the same 6,000-frame scripted Banshee sequence, A1200 interpreter,
PAL fullscreen and Paula audio. Private test hosts suppress external gameplay
input; installed controls remain unchanged.

| Build | Whole-run emulated FPS | Change | Audio late-submit gaps |
|---|---:|---:|---:|
| Current pixel-loop reference | 36.950 | — | 2,060 |
| Denise once | 36.316 | -1.72% | 2,099 |
| Outlined AGA64 fetch | 36.321 | -1.70% | 2,154 |
| Table-driven fetch dispatch | 36.591 | -0.97% | 2,075 |

All three candidates fail the performance gate. These individual comparisons support
rejecting promotion, not an exact universal regression or a proven cause.
Reduced source work and smaller executable code did not translate into faster
execution in these runs.

All runs match 116,472,634 dispatches, 814,003,022 guest cycles, PC `00029056` and
framebuffer SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
All 3,330,048 PCM sample frames were queued, submitted and completed with device
error zero. Gaps remain; completed delivery does not establish audible quality.
Register/MMU/cache-witness restoration and memory release passed.

## Follow-up

A table-driven candidate reuses UAE's existing `cycle_sequences` array instead
of nested per-plane dispatch switches. Unlike outlining, it retains an inline
fetch body. Native source-block comparisons pass 940,032 combinations, including
idle cycles and reserved plane counts. Four ARM fixtures, PAL/NTSC mixed-mode
comparisons and the nonempty PCM comparison pass. Generated per-cycle function
sizes are 2,380, 2,360 and 2,572 bytes for the three fetch modes, versus 6,980,
6,756 and 7,436 bytes in the reference.

The physical follow-up completed with matching guest state/pixels and all PCM
delivered, but ran 0.97% slower than the reference. It also remains private.
Replacing the dispatch switches did not establish an end-to-end benefit.

## Outcome and next investigation

Five physical runs completed: one diagnostic, one reference and three candidates,
totalling 30,000 guest frames. Temporary players were removed, Core1 is free,
and the installed normal/FPU hashes were verified unchanged. No product version,
release or firmware change follows from these experiments.

The next useful step is to distinguish cost within the per-cycle path: actual
ChipRAM fetches, output shifting/flushing, and event/state bookkeeping. The profile
above does not separate those costs. Another code-size change without that
evidence would repeat an unsupported premise. Preserve all guest-visible events;
do not infer that idle-cycle work or unshown scanlines can simply be discarded.

[Build scripts, patches, model results and hardware logs](bitplane-spans/).
