# State of the Art: drawing cadence and bitplanes

This 0.5.4-dev investigation separates the **displayed frame rate** from the
PAL guest's CPU/chipset/audio timing. Selecting 30 FPS permits more display
updates; it does not make a 50 Hz PAL demo execute at 30 Hz.

## Changes investigated

1. **Measure inclusive stages.** Timers around drawing, bitplane conversion,
   Paula, PCM publication, final conversion and presentation identified the
   available rendering savings. Profiled binaries are diagnostic only.
2. **NEON bitplane transpose.** Adapt the pinned UAE4ARM routines for 2–6 planes,
   using an explicit source address and preserving D0–D31 and FPSCR. Existing
   access-policy checks decide whether to use NEON; no firmware registers are
   enabled or changed. Scalar fallback handles other cases. This is an opt-in
   experiment: the first physical run was slower, so it is not promoted.
3. **Choose drawing cadence before drawing.** Skip partial/final pixel drawing
   for frames that the 25/30 FPS selector would discard. CPU execution, Copper,
   Blitter, Paula, line recording and input handling continue. The existing
   late audio-reserve check can still defer presentation. Bounded diagnostics
   draw their final frame even if the cadence would skip it.
4. **Initialize a per-run clock epoch.** UAE's previous-frame time initially
   equalled zero while its current time came from board uptime. The signed
   high bit could make the first time delta look negative and lose one counter
   increment. A model reproduced an extra guest frame with high initial uptime.
   Establishing an epoch before custom-chip initialization fixes this endpoint
   discrepancy. It is not an emulation-speed optimisation.

The new launcher default is 30 FPS. The 25, 50 and MAX choices remain available.
Existing installations retain their saved choice unless explicitly changed.

## Matched hardware result

Both builds below include the clock-epoch fix and use the same 30 FPS cap,
3,000 guest frames, fullscreen, original State of the Art disk, A500/Kickstart
1.3, 512 KiB Chip + 512 KiB Slow, AHI 32 kHz stereo and Soft software scanlines.
Each was run twice. The displayed rate uses total presented frames divided by
its host observation interval; it is not the guest-frame counter.

| Build | Displayed FPS, run 1 / run 2 | Combined FPS | Late audio observations, run 1 / run 2 |
|---|---:|---:|---:|
| Prior drawing path | 18.53 / 18.39 | 18.46 | 209 / 213 |
| Early drawing selection | 19.88 / 19.60 | 19.74 | 134 / 113 |

**6.93% more displayed frames per second** at the same setting. Both updated
runs drew 1,800 frames and skipped 1,200 before drawing. All four runs executed
29,718,700 guest instructions and 372,192,964 cycles, ended at PC `0004529e`,
produced framebuffer hash `1ec83040` and completed 1,922,048 PCM frames, including
1,078,677 nonzero frames. Captured final pixels match byte-for-byte; repeat-run
framebuffer CRC was `4B424AAC`. No device, SIMD, cache/MMU restoration or owned
memory-release errors were reported.

Early drawing is now the normal compatible-player build path; NEON bitplanes
remain off. **30 FPS is a target, not an achieved average for this sequence.**
The two-run sample supports this measured improvement, not a general speed
claim for all games or a claim of glitch-free audio. The experimental JIT
player keeps its previous drawing path and installed binary.

## Profiling and preliminary experiments

A 3,000-frame instrumented fullscreen run used A500/Kickstart 1.3, 512 KiB Chip
plus 512 KiB Slow RAM, AHI 32 kHz stereo and Soft software scanlines. Its ~63-second
wall time included approximately 11.1 seconds inside drawing, 1.44 seconds inside
bitplane conversion, 5.05 seconds inside audio, 2.25 seconds inside PCM publication,
3.63 seconds inside final pixel conversion and 6.47 seconds inside presentation.
**These stages overlap and must not be added together.** Drawing minus nested
presentation was about 4.63 seconds. The profile therefore did not support a
large whole-demo speed claim from NEON bitplane conversion alone.

Preliminary displayed rates were 15.65 FPS at the old 25 FPS cap, 17.94 FPS at a
30 FPS cap, 16.23 FPS with NEON bitplanes, 17.32 FPS with NEON plus early drawing,
and 20.13 FPS with early drawing and the existing scalar bitplane converter.
The last run exposed the one-frame timer discrepancy above. These exploratory
runs are retained as evidence, not the final matched performance comparison.
All final RGB565 captures were byte-identical; the temporary screens closed and
cache/MMU/register restoration and owned-memory release passed.

## Verification

- Actual ARM leaf: 2–6 planes, every word count from 0 to 50, independent pixel
  oracle, source/destination guards and D0–D31/FPSCR/integer callee preservation.
- Native cadence arithmetic and launcher configuration under ASan/UBSan.
- Actual ARM worker: CPU/CCR, Chip RAM, final pixels and PCM comparisons at
  25/30 FPS, odd bounded endpoints, audio pressure, input, delayed ACK,
  cancellation and invalid-option handling.
- Initial timer epoch regression: equal execution with low and high initial
  board uptime. Synthetic model tests require no supplied ROMs or ADFs.
- Framework and instruction-audit tests. The generator has CC4; no duplicate
  candidates at threshold 0.8; five of five generator mutations were killed by
  generating, assembling and executing the ARM code. These Python metrics are
  not a coverage claim for the emulator.

Late AHI queue observations are diagnostics, not measured audible dropout
lengths. Listening and visual acceptance remain separate from automated checks.
The matched repeated fullscreen sequence covers startup and the opening
animation, not the entire demo. A longer 6,000-frame windowed candidate run
completed in 142.49 seconds and presented 1,717 frames (12.05 FPS), with
752 late audio-queue observations. Later sections remain significantly slower;
this is a remaining performance problem, not a full-speed compatibility claim.
The matched previous-path windowed run presented 1,591 frames in 144.79 seconds
(10.99 FPS), with 1,039 late audio observations. This longer single-pair
comparison improved displayed FPS by 9.67%. Both executed 55,367,330 guest
instructions / 724,050,660 cycles, ended at PC `0004027c`, completed 3,845,120
PCM frames and produced framebuffer CRC `9833DD65`. Both released owned memory
and passed cache/MMU/register restoration. The longer windowed average and
shorter fullscreen average cover different sequences and cannot isolate a
window-versus-fullscreen performance difference. Guest JIT and fullscreen buffer flipping are separate work; this change
continues using the existing offscreen bitmap and host blit.

## Reproducing the build variants

```sh
# Normal compatible player: early drawing, existing final-pixel NEON conversion
python3 scripts/build_uae4arm.py
python3 scripts/build_uae4arm_machine.py --hardware

# Previous drawing cadence (retains the clock fix)
python3 scripts/build_uae4arm.py --late-draw
python3 scripts/build_uae4arm_machine.py --hardware

# Experimental bitplane NEON; deliberately not the normal build
python3 scripts/build_uae4arm.py --neon-bitplanes --late-draw
python3 scripts/build_uae4arm_machine.py --hardware
```

Build/run evidence and the action record are in
[the test records](../amiga/records/2026-10-27/uae4arm/state-of-art/).
The separate [PJIT review](amiga-uae4arm-pjit-review.md) records another CPU-path
research reference; no PJIT code is included in these builds.
