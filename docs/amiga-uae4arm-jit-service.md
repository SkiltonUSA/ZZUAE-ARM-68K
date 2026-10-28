# JIT service timing and frame drawing

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

This follow-up separates special-service costs and tests drawing cadence and
register-only trace coverage. It builds on the
[precomputed opcode cycle map](amiga-uae4arm-jit-profile.md).

## What special service contains

The optional profiler now measures STOP and explicit Copper calls inside
`do_specialties()`. These are **inclusive** intervals within the original
special-service bucket. STOP may itself contain Copper calls. Do not add the
seven counters as independent percentages; only the first five are exclusive.
The JPR2 report contains seven counters in the existing 128-byte report area.

| Workload | STOP share of special service | Explicit Copper share of special service |
| --- | ---: | ---: |
| Frontier, 3,000 guest frames | 92.06% | 2.31% |
| Alien Syndrome, 1,800 guest frames | 83.65% | 2.09% |
| A600 / Workbench 2.0, 1,800 guest frames | 93.56% | 1.48% |

STOP advances guest cycles and services the chipset, drawing and audio. These
samples do not identify removable interrupt overhead. Copper processing called
elsewhere is not included in the explicit Copper subcounter. The measurement
therefore does not justify reducing interrupt checks or skipping chipset work.

| Workload | Uninstrumented | Profiled | Profiling overhead |
| --- | ---: | ---: | ---: |
| Frontier | 54.420246 s | 54.854471 s | +0.80% |
| Alien Syndrome | 31.547979 s | 32.172388 s | +1.98% |
| Workbench 2.0 | 21.705648 s | 22.183214 s | +2.20% |

Each cell represents one fresh-process hardware run using the precomputed
cycle map, 32 MiB executable cache and 64 MiB allocation, without live display
or audio. Dispatch counts, guest cycles, final PC and frame hashes agree.
All six runs restore registers/MMU/cache state and release their allocation.
Performance comparisons use uninstrumented binaries.

## Candidates

- `--early-draw`: apply the normal player's existing 25/30/50/MAX drawing
  cadence to the experimental JIT build. Guest CPU, chipset and Paula still
  execute every guest frame. Bounded tests retain their final framebuffer.
- `--register-groups`: allow fixed-cycle register bit operations, shifts,
  rotates and Scc in event-bounded traces. Memory operands, variable-cycle
  instructions, control flow, SR changes and exception instructions retain
  their existing boundaries.

## Verification details

The service sampler has native tests for inactive clocks, nested intervals,
32-bit timer wrap and 64-bit accumulation. The source transform has unit tests
and 11/11 selected Python mutations caught. These metrics do not cover the
C++ implementation. ARM instruction-model checks separately cover CPU results,
cancellation, faults, executable-page restoration and chipset timing.

A new bit/shift timing fixture initially disagreed only on unused bits in the
X-flag backing word. The pinned ARM `GET_XFLG()` reads bit zero. The test now
compares architectural X rather than unrelated backing bits, just as it masks
NZCV to bits 31–28. Guest registers, actual flags, cycles, RAM and pixels agree.
The CPU differential fixture now seeds X both set and clear; earlier seeds
placed it in bit 29 and therefore did not exercise incoming X=1.

## First live comparison

Alien Syndrome, 3,000 guest frames, windowed, 30 FPS presentation, AHI 32 kHz
stereo, using fresh processes:

| Variant | Elapsed | Frames drawn | Display presentations | Late AHI submissions |
| --- | ---: | ---: | ---: | ---: |
| Precomputed cycle map | 75.953433 s | 3,000 (drawing always enabled) | 954 | 782 |
| Plus early drawing | 76.556039 s | 1,800 | 1,037 | 772 |

Early drawing skipped 1,200 draws but produced more presentations under the
existing audio-pressure policy. Total throughput was 0.79% lower in this pair;
it is not a measured optimisation by itself. Both runs produced identical
cycles, PC, final pixels and nonzero-PCM count, with 1,922,048 PCM frames queued,
submitted and completed, no backend errors and clean teardown. Late-submission
counts are diagnostic observations, not measured audible-gap durations. These
runs were not auditioned.

A larger audio prebuffer cannot fix a sustained producer-rate deficit: this
workload generates about 60 seconds of PCM in roughly 76 seconds of elapsed
time. The next experiment moves audio-pressure decisions before pixel drawing,
while retaining the bounded refresh policy and guest-frame execution.

## Register-group results

The expanded whitelist produced these matched hardware endpoints. The timings
are one fresh-process run per variant, not a statistical confidence interval.

| Workload | Precomputed map | Expanded register groups | Throughput gain |
| --- | ---: | ---: | ---: |
| Frontier, 3,000 frames, headless | 54.420246 s | 53.357499 s | +1.99% |
| Alien Syndrome, 1,800 frames, headless | 31.547979 s | 30.502847 s | +3.43% |
| Workbench 2.0, 1,800 frames, headless | 21.705648 s | 21.643874 s | +0.29% |
| Alien Syndrome, 3,000 frames, window/AHI | 75.953433 s | 73.666965 s | +3.10% |

The live candidate reduced dispatches from 30,692,623 to 27,441,205, with identical
guest cycles, PC, final framebuffer and nonzero-PCM count. All 1,922,048 queued
PCM frames completed. Late AHI submission observations fell from 782 to 733;
this is still not stable-audio evidence. Cleanup passed.

## Decide audio-pressure skips before drawing

`--early-draw --early-pressure` moves the existing reserve/streak decision to
the start of a drawing frame. It retains the first presentation, bounded refresh
and final-frame drawing; input remains serviced on skipped frames. The default
late-pressure path remains available for comparison.

The model's 12-frame pressure fixture initially failed the new check on the
old implementation (seven draws, five skips). The candidate draws five and
skips seven, with matching final CPU/RAM/pixels/PCM, stereo DMA, ordered input
and bounded refresh. Six chipset timing fixtures and the strengthened CPU suite
also pass.

On hardware, the 3,000-frame window/AHI run took **74.612091 seconds**, **1.80%**
faster than the 75.953433-second baseline. It drew and presented 1,113 frames,
skipping 1,887 draws. All 1,922,048 PCM frames completed, with 749 late submission
observations, no backend error and clean teardown. This is a separate candidate;
its percentage must not be added to the register-group gain. Their combination
had not been measured at this stage. The subsequent
[combined-build report](amiga-uae4arm-jit-batch.md) measures the combination.

## Long-run gate

The register-group candidate still reached the unchanged **150-second timeout**
in the requested 6,000-frame window/AHI run. This is a failed completion gate,
not a successful 6,000-frame benchmark. Before stopping, 3,446,784 PCM frames were
queued, submitted and completed; 2,204 late-submission observations were recorded.
The frontend stopped with exit 20, removed input handling, restored all MMU/cache/
register witnesses and released its allocation. A separate postflight found Core1
idle and the existing Workbench applications/settings intact.

The timeout was not increased. No launcher default, installed player or release
package is promoted by these results. The compatible 68000 player remains the
normal default. Stable JIT acceptance still needs the long live/audio gate and
broader compatibility testing. The subsequent 0.5.5 Beta packages the modes as
optional experiments; it does not claim to pass this gate.

## Longer headless compatibility checks

A600 / Kickstart 2.05 / Workbench 2.0 completed **5,400 guest frames** in
53.901494 seconds with the matching 68020 interpreter and 57.173053 seconds
with register-group JIT. Guest cycles (767,306,319), PC (`00f8115c`) and final
frame hash (`243cedd8`) match, with clean teardown. The JIT is still slower
than the interpreter here. This is a bounded desktop execution check, not
coverage of every Workbench application or peripheral.

## Reproduce the candidates

```sh
python3 scripts/build_uae4arm_jit.py --event-blocks --cache-kib 32768 \
  --movw-constants --armv7-emitter --flat-cycles --register-groups \
  --player --hardware
```

Replace `--register-groups` with `--early-draw --early-pressure` for the separate
scheduling candidate, or `--jit-profile` for the sampled service build.
`--early-pressure` requires `--early-draw`; register groups require event blocks.
These builds retain separate output directories and need 64 MiB of available
ZZ9000 RAM. Never run another Core1 application concurrently.

Native tests cover classification boundaries, sampling, nested intervals and
longjmp abandonment. The final profiler uses explicit interval completion,
with a trivial destructor, so guest exception unwinding does not bypass a C++
destructor. Interrupted intervals are omitted rather than treated as completed.

The attempted 6,000-frame headless Frontier reference reached its existing
20-million-dispatch guard at frame 3,226, then restored state and exited normally.
The harness correctly rejected it as an incomplete frame-target test despite
process exit 0. No 6,000-frame Frontier compatibility result is claimed, and the
candidate was not compared against that truncated reference.
