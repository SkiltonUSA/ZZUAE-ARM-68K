# State of the Art: coloured-tile slowdown

Investigation on 28 October 2026. The affected scene follows **LOTSA KRAYZ CODE**:
a dancer over changing coloured tiles. It appears around guest frames 3,400–3,800
(68–76 seconds at 50 Hz), later than the initial estimate.

## What is affected

These findings concern **Copper emulation inside ZZUAE on the Cortex-A9**.
They are not evidence of a defective Copper chip, ZZ9000 or FPGA firmware.
The demo's Copper list waits for beam positions and changes display registers
while CPU and DMA activity continue. ZZUAE must preserve the order of those
operations even when several changes occur within a scanline.

The symptom is a severe slowdown in the changing-colour dancer scene, accompanied
by audio starvation. The separate background RAM-disk stall was resolved before
these comparisons; it does not explain the scene-specific Copper cost measured
here. The corrected predictor reduces overhead but does not remove the need to
emulate those register changes and DMA interactions.

## Issues and fixes

| Issue | Evidence | Change / remaining limitation |
|---|---|---|
| Dense Copper activity consumes ARM time | 4.91 million update calls in the 400-frame slow interval; about 60% of profiled time | Predict future Copper events; finer profiling of DMA decisions and register writes remains necessary |
| WAIT shortcut could lose state | Original fast path returns before the common state-commit code | Reach the normal state commit rather than returning early |
| WAIT shortcut could lose cycle alignment | A CPU horizontal position can be odd while the Copper advances in two-cycle steps | Preserve Copper alignment when advancing towards a WAIT target |
| CPU/Copper ordering changed pixels | Synthetic colour-write and combined list-write/COPJMP cases failed with original fast mode | Synchronize pending Copper work on CPU custom-register access; remove first-sync/register-type early-outs in this optional mode |
| Frames were drawn and then discarded | Reference draws all 6,000 frames but presents only 2,172 under audio pressure | Make the same bounded pressure decision before drawing; keep all chipset/CPU/audio work |
| Slow-scene presentation and audio gaps persist | Profiled conservative variant presents about 4.1 FPS; starvation counters remain nonzero | Do not describe this as full-speed playback or a complete Copper fix |

## Diagnosis

A completed 6,000-frame run on the ZZ9000 isolates a large increase in **Copper
execution**, rather than final pixel conversion. It used the compatible A500
player, Kickstart 1.3, 512 KiB Chip + 512 KiB Slow RAM, Paula audio, a 640×480 window
and a 50 FPS display cap. RAM-disk Info queries were 23–28 ms before testing.

| Profiled interval | Guest FPS | Displayed FPS | Copper share of elapsed time |
|---|---:|---:|---:|
| Before: frames 3,000–3,300 | 41.48 | 10.37 | 0.81% |
| Coloured tiles: frames 3,400–3,800 | 13.51 | 3.38 | 59.57% |
| After: frames 3,900–4,100 | 39.67 | 9.92 | 0.37% |

The dense 400-frame interval makes 4.91 million Copper-update calls and records
1.77 million colour changes. Copper execution takes 17.64 s of 29.61 s elapsed;
colour-span drawing takes 0.77 s. These are **instrumented diagnostics**, not
release-build benchmark figures. Inclusive stages overlap and cannot be added.

The audio-reserve policy also defers presentation: 100 of those 400 guest frames
reach the window. This compounds the visible slowdown. All guest frames are
still drawn at this setting before the late audio-pressure decision.

## Implementation

The pinned UAE4ARM core contains a `fast_copper` predictor. Enabling it unchanged
passed the demo's 29 sampled images and final guest-state check, but failed a
synthetic CPU/Copper colour-write regression. It is not suitable as a default.
The regression also combines Copper-list writes and COPJMP restarts; comparing
only a final picture would miss some errors.

The candidate retains event prediction and synchronizes pending Copper work on
CPU custom-register accesses without the predictor's register-type/first-sync
early returns. Its horizontal WAIT jump preserves the Copper's two-cycle phase
and commits state normally instead of returning early. Guest instruction and DMA
timing remain on the existing compatible A500 path.

An intermediate conservative variant disabled WAIT jumping entirely. It helped
isolate the ordering bug; the final variant restores only the aligned WAIT jump.

A separate change moves the existing audio-reserve decision before drawing. It
avoids rendering a frame that would be discarded immediately afterward. CPU,
Copper, blitter and Paula still execute every guest frame. The existing maximum
of three consecutive pressure skips remains; the final diagnostic frame is drawn.

The source build switches remain opt-in. The **0.5.7 Beta compatible player**
is packaged with both enabled; JIT/FPU algorithms are unchanged:

```sh
python3 scripts/build_uae4arm.py --copper-predict --early-pressure
python3 scripts/build_uae4arm_machine.py --hardware
```

Omit `--copper-predict` to measure early drawing selection alone. Preserve a
reference ELF before rebuilding. With Unicorn installed, the synthetic regression
suite needs no external Kickstart or disk:

```sh
python3 tests/amiga/uae4arm/check_copper.py \
  reference.elf candidate.elf results/copper
```

It checks horizontal WAITs, taken/untaken SKIPs, CPU colour writes, COPJMP restarts,
combined writes, alternating Copper-list modifications and WAITs past the line end. With audio disabled it
compares every presented frame. Its audio-pressure case compares CPU/CCR, RAM,
final pixels and PCM. Instruction-model tests do not replace physical checks.

## Uninstrumented physical comparison

Same 6,000 guest frames, A500/Kickstart 1.3, 512 KiB Chip + 512 KiB Slow, Paula,
640×480 window and 50 FPS cap. No bridge screenshots or status polling during the
measured interval. Each row is one completed run, not a statistical average.

| Build | Elapsed | Displayed frames | Mean displayed FPS | Audio gap counter |
|---|---:|---:|---:|---:|
| Reference | 148.726 s | 2,172 | 14.60 | 1,603 |
| Early audio-pressure drawing selection | 140.803 s | 2,376 | 16.87 | 686 |
| Conservative prediction + early selection | 139.992 s | 2,329 | 16.64 | 798 |
| Aligned WAIT prediction + early selection | 138.550 s | 2,379 | 17.17 | 686 |
| Aligned WAIT, source-build repeat | 138.502 s | 2,390 | 17.26 | 673 |

The drawing-only change takes **5.3% less time**, with **15.6% higher average
displayed FPS** across this complete sequence. It skips 3,624 drawing operations.
All five runs execute 55,367,330 guest instructions and 724,050,660 guest cycles,
finish at PC `0004027c`, and produce identical final raw-frame SHA-256. All deliver
all 3,330,048 PCM frames, report device error 0 and pass register/MMU/cache-witness
restoration and owned-memory release. The gap counter still records starvation;
this is not a claim of uninterrupted audio or a complete fix for the tile scene.

The conservative combined candidate is only 0.6% faster in elapsed time than
early drawing alone, and presents fewer frames. A single run does not establish
an additional predictor benefit. The aligned WAIT variant takes 1.6% less time
than drawing selection alone. The source-build repeat completes in 138.502 s:
6.9% less time and 18.2% higher average displayed FPS than the reference. The two
aligned runs agree closely, but there is only one uninstrumented reference run.
Neither variant fixes the slow scene completely. Source builds require explicit
flags; the 0.5.7 Beta compatible-player package enables the corrected variant.

A separate instrumented scene comparison confirms that the coloured-tile section
is still far from full speed:

| Frames 3,400–3,800 | Guest FPS | Displayed FPS | Copper time |
|---|---:|---:|---:|
| Fresh reference profile | 13.47 | 3.37 | 17.64 s |
| Conservative prediction + early selection profile | 16.41 | 4.10 | 15.28 s |

The combined profile completes all 6,000 guest frames and passes cleanup. These
scene numbers contain timer overhead and must not be substituted for the
uninstrumented whole-sequence results. Fewer Copper calls also mean fewer timer
reads. The effect still needs substantial work; this is an incremental result.

The original, unsafe predictor's profiled tile interval improved from about 13.5
to 16.4 guest FPS. This is diagnostic only: reducing calls also removes profiling
timer overhead, so it is not a release-build speedup claim.

## Measurement limitations

An initial longer profile hit the original 150-second test timeout and is excluded.
The completed profile uses a private 450-second timeout and exits 0 with all
register/cache/MMU witnesses restored and owned memory released.

A later uninstrumented comparison is excluded: it was cancelled before the frame
target, with a leftover diagnostic shell from a filename collision present.
Test filenames now respect the 30-character filesystem limit, and the runner
requires completion of the requested guest frames as well as clean teardown.

## Next target

Split the `update_copper` profile into instruction fetch/WAIT processing,
DMA/bitplane decisions and custom-register writes. Optimise the dominant section
while retaining cycle order and the CPU-write regressions. Pixel conversion is
not the main bottleneck in this scene. Changing the display cap alone does not
remove the required Copper/Paula/CPU emulation work.

## Final state

ARM/68k build and context-instruction audit pass; eight Copper regression cases,
25/30/50 FPS audio-pressure tests, 23 shared ARM tests and the MCP simulator smoke
pass. The physical runs restore registers/MMU/cache state and release their owned
allocation. Audio gap counters remain nonzero; listening and wider compatibility
tests are still needed.

The tested optimisations were installed successfully on the A4000TX. A subsequent
unlimited-play check passed audio delivery and cooperative exit. The 0.5.7 Beta
packages contain the same implementation with updated version identification.
Machine-readable results and test summaries are in
[`amiga/records/2026-10-28/uae4arm/copper-comparison`](../amiga/records/2026-10-28/uae4arm/copper-comparison/).


## Source and regression coverage

The starting point is the pinned
[UAE4ARM Copper implementation](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/src/custom.cpp).
The ZZUAE changes are in [Copper preparation](../scripts/prepare_uae4arm_copper.py)
and [live drawing selection](../amiga/uae4arm/live_arm.cpp).
[Synthetic fixtures](../tests/amiga/uae4arm/copper_fixture.py) and the
[ARM comparison runner](../tests/amiga/uae4arm/check_copper.py) reproduce the
ordering checks without game disks or Kickstart files.
