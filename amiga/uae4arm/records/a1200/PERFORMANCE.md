# A1200 performance investigation

These are physical A4000TX/ZZ9000 development measurements. The A1200 profile
is experimental; a successful test does not establish full game compatibility.

## Method

The matched runs use Kickstart 3.1 (40.68), 2 MiB Chip RAM, PAL, the 68020
interpreter with upstream's 14 MHz CPU/chipset ratio, and native 320×256
fullscreen output. Performance comparisons initially disable sound. Audio-paced
runs are separate because they can skip presentation while continuing emulation.

The private harness sends input at fixed **guest frame numbers**, rather than
wall-clock times. Banshee's comparison runs request 6,000 guest frames. The
last 3,000 frames cover the in-game scene; startup averages include disk loading
and menus. The reported rate is completed **emulated frames per second**, not
a counter inside the game or the monitor's refresh rate. Presentation is capped
at 50 FPS for these PAL tests.

The common input schedule presses/releases left mouse at frames 900/910,
1800/1810 and 2800/2810, fire at 3200/3210, 4000/4010 and 4800/4810,
Return at 3600/3610 and Space at 4400/4410. The extended Slam Tilt pair adds
left mouse at 3800/3810 and Return at 5200/5210 to both candidates.
These deterministic test players are separate from the installed application.

Each run checks completion, display errors, Core1 register/MMU/cache restoration
and allocation release before starting another. Final raw frame hashes and CPU
diagnostic results are compared. An instruction-limit stop is reported separately
from completing the requested frame count. No physical-controller or listening
acceptance is inferred from scripted input and audio counters.

The completed fixed-frame series contains 23 runs and 127,000 emulated
frames (3,742 seconds of reported run time), plus separate navigation, fixture
and FPU checks. All 23 fixed-frame runs passed teardown checks. This count
excludes the rejected 8,000-frame command and the earlier instruction-bound run.

## Renderer candidates

- **NEON bitplane conversion:** adapts the pinned UAE4ARM transpose routines for
  two through eight planes. Feature detection respects the existing XACP NEON
  policy; unsupported cases retain scalar conversion. The assembly leaf restores
  every SIMD register and FPSCR.
- **NEON native-resolution conversion:** adds a 320-pixel RGB565-to-RTG leaf to
  the existing 640-pixel path. Interleaved loads select the same even source
  pixels as the scalar 640-to-320 mapping. Pixel selection and aspect ratio are
  unchanged. Row conversion stays in cached private RAM before writing the
  currently granted bitmap.

The third candidate specialises **emulated Chip RAM reads** in the 68020
interpreter. It tests the current memory-bank pointer, then performs the same
masked big-endian read inline. ROM and device banks retain their callbacks;
writes, invalidation and device side effects are unchanged. This reduces
indirect-call overhead; it is not physical DMA or a new JIT implementation.
Only the main interpreter opcode unit enables it. The reproducible build's
CPU object is byte-for-byte identical to the private hardware-test candidate.

The candidates remain independently selectable at build time:

```sh
python3 scripts/build_uae4arm_a1200.py --neon-bitplanes --neon-half --chip-reads
```

Instruction-model checks cover PAL/NTSC AGA output, scalar/NEON CPU and RAM
state equivalence, the RGB565 colour range, both RTG pixel formats, row bounds,
source preservation, cancellation, framebuffer ownership and D0–D31/FPSCR
restoration. The native instruction audit rejects SIMD outside the approved
assembly leaves.

## Matched Banshee results

| Rendering path | Whole-run emulated FPS | In-game interval emulated FPS |
|---|---:|---:|
| Scalar bitplanes and native-resolution conversion | 29.91 | 25.18 |
| NEON bitplanes | 30.28 | 25.39 |
| NEON bitplanes and native-resolution conversion | 31.01 | 26.04 |
| Both NEON paths plus inline Chip RAM reads | 31.73 | 26.76 |

These runs reached the same final game image and identical CPU diagnostic
results. The two NEON changes were 3.7% faster across the complete sequence
and 3.4% faster in the final interval.
A second NEON-only run measured 31.01 FPS overall and 26.00 FPS in the
late interval. The second Chip RAM run measured 31.73 FPS overall and about
26.76 FPS in that interval. Both repeated the same final image and CPU state.
The complete candidate is approximately 6% faster than the initial scalar
sequence; the incremental memory-read gain is approximately 2.3% overall.
These figures describe this workload, not all AGA software.
They do **not** establish real-time PAL performance.

A separate instrumented run attributed approximately 23% of elapsed time to
drawing and presentation, including 1.5% to bitplane conversion. These inclusive
timers overlap and include waiting; their percentages must not be added together.
This makes CPU/chipset work the next target, rather than further bitplane tuning
alone. The instrumented build is not the performance baseline.

## Matched Slam Tilt loading result

The extended input schedule completed 6,000 guest frames in both builds:

| Path | Elapsed seconds | Emulated FPS |
|---|---:|---:|
| Scalar baseline | 153.67 | 39.05 |
| NEON conversion plus inline Chip RAM reads | 144.22 | 41.60 |

That is a 6.6% throughput improvement. CPU dispatch count, cycles, final PC and
pixels match. The sequence ends on a black loading transition, so this is a
**loading-sequence result**, not pinball gameplay FPS. The separate navigation
run below reached the table. An attempted 8,000-frame extension was rejected
by the player's 6,000-frame command-line limit before emulation started; it is
not a completed run or a hardware failure.

## Media setup

The supplied 1869 disks boot to Workbench. A private startup copy launches the
unchanged game executable. Its first test requested disk D. A separate read-only
HDF containing all four disk directories, with the appropriate DOS assigns,
reached the new-game player selection screen. This is an installation/loading
fix, not a change to the game or emulated CPU.

Original disk images remain unchanged. Game media and ROMs are not included in
these development records.

## Candidates not promoted

- The existing partial JIT took 95.46 seconds for the first 3,000 Banshee
  frames, compared with 78.22 seconds for the interpreter at the same point
  (22% longer). The interpreter remains the A1200 default. This is a startup
  comparison, not a JIT gameplay measurement.
- Recompiling only the main CPU opcode unit with `-O3` produced 31.03 FPS
  against 31.01 FPS with `-O2`, with identical final state. That difference
  is too small to establish an improvement, so the compiler setting is retained.

- Reusing fast Copper prediction for the A1200 interpreter passed horizontal
  WAIT and SKIP comparisons but failed the CPU colour-write fixture: final
  pixels and presented-frame hashes differed. It was **not promoted or run
  on hardware**. The new `check_copper.py --a1200` mode retains this regression
  check for future work. Existing Copper behaviour is preserved.

## Audio-paced checks

| Run | Guest frames | Elapsed seconds | Emulated FPS | Displayed frames | Audio gap counter |
|---|---:|---:|---:|---:|---:|
| Banshee demo, Paula | 6,000 | 167.86 | 35.74 | 2,266 | 2,134 |
| Arcade Pool credits, Paula | 5,000 | 121.88 | 41.02 | 1,855 | 1,952 |

Both runs delivered all queued PCM and reported no device error, but their
completion counters do not imply uninterrupted audio. The worker's gap counter
records when the preceding stereo block has already completed before its
successor is queued. These runs fall short of real-time guest speed and contain
many such events. Larger buffers alone cannot sustain playback when the producer
is consistently slower than the emulated audio clock. Audible quality still
requires listening. The displayed frame rates were approximately 13.5 and
15.2 FPS respectively; audio-driven presentation skipping explains why the
emulated rate rose above the sound-disabled test.

## Wider loading checks

The following use the combined NEON build, sound disabled and the same native
fullscreen mode. These rates include loading. They are not game-engine FPS.

| Supplied title | Requested guest frames | Whole-run emulated FPS | Observed endpoint |
|---|---:|---:|---|
| 1869 AGA, four-disk HDF installation | 6,000 | 34.64 | New-game player selection |
| Banshee playable demo | 6,000 | 31.01 | In-game flying scene |
| Banshee four-disk release, disks 1/2 attached | 5,000 | 35.55 | Main menu |
| Arcade Pool | 5,000 | 36.11 | Credits |
| Alien Breed 3D, disks 1/2 attached | 5,000 | 21.03 | Insert-level-disk prompt |
| Alfred Chicken AGA | 5,000 | Not accepted | Trainer passed; final frame black |
| Slam Tilt playable demo | 5,000 | 39.67 | Controls/instructions screen |

Every row completed the requested frame count and clean Core1 teardown. That
establishes transport/lifecycle completion, not successful gameplay for every
title. Alien Breed 3D still requests the level disk with its second disk in DF1;
loading it into DF0 needs a separate swap/loading check. Its final title-screen
intervals were approximately 15–17 emulated FPS. Alfred Chicken's black-frame
rate is deliberately excluded from the performance table.

The first Arcade Pool run requested 6,000 frames but reached the harness's
200-million-dispatch safety bound at frame 5,472. It exited cleanly and was
rerun with an explicit 5,000-frame target. The shorter run must not be described
as a completed 6,000-frame test.

[Machine-readable results and per-run logs](performance/results.json).

## Navigation follow-up

Separate runs sent keyboard/mouse events through the player's own IDCMP port,
without Workbench input injection. These were navigation checks, not matched
performance runs:

- Banshee reached the first mission briefing after its menu and high scores.
- Slam Tilt reached the pinball table; keyboard events were delivered before
  a clean exit. The earlier black frame was a loading transition in this case.
- Arcade Pool reached configuration and credits; the pool table is not yet
  validated by these runs.
- 1869 reached player selection with zero HDF I/O errors. Press Space at the
  opening screen, then choose the number of players.
- Alfred Chicken ended on the same black frame, with identical CPU diagnostics,
  in both scalar and NEON runs. It is not a new renderer regression; the cause
  remains under investigation.

All navigation runs returned to Workbench and released Core1 cleanly.

Removing SetPatch from a disposable Alfred Chicken startup disk also left the
final frame black. This did not resolve the compatibility issue; the original
disk and normal startup remain unchanged.

## Captured screens

Slam Tilt playable demo, table reached during the navigation check:

![Slam Tilt table](performance/slam-tilt-table.png)

Banshee full release, first mission briefing:

![Banshee mission briefing](performance/banshee-briefing.png)

## Installed experimental build

The 0.6.0-dev A1200 players now include both NEON converters and inline Chip
RAM reads. The normal player and matching FPU player passed physical checks;
PAL/NTSC AGA fixtures passed in both window and fullscreen, with zero SIMD
state errors and clean Core1 restoration. They were copied with transfer-hash
verification to `SD032G:Emulator/ZZUAE/A1200-Test`. The canonical 0.5.7 drawer
was not replaced. Private input/benchmark executables were removed after testing.

[Installed executable hashes](performance/installed-chip-builds.json).
The optional FPU build uses `build_uae4arm_fpu.py --base` pointing to the recorded
`-neonplanes-neonhalf-chipreads` build, so it shares the same core, flags and
0.6.0-dev product version. No release was published during this test series.

The follow-up [gameplay profile](GAMEPLAY-PROFILE.md) separates instruction
execution from scanline, bitplane, audio and other chipset work.
