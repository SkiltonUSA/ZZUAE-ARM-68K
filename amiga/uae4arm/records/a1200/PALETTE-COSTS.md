# Palette and line-clear costs on the A4000TX

The [buffer audit](BUFFER-AUDIT.md) identified changed-palette copies as a
profiling candidate. A separate instrumented player now measures that path during
Banshee gameplay. The installed normal and FPU players remain unchanged.

## Method and validation

The private build starts from `build-pixel4`, retaining its interpreter, 32 MiB
translation cache, NEON paths and 64 MiB allocation. Timers sample approximately
one in 64 calls after emulated frame 3000. Compiler memory barriers surround the
timer reads. An empty timer scope estimates the measurement floor. Inclusive
stages contain their child copy stages; do not add them together.

Two 16-frame direct-output model comparisons (fine pixels and Copper colours)
match reference CPU, RAM, pixels and all acknowledged frame hashes. Timers are
inactive during those short warm-up checks. The physical 6000-frame PAL Banshee
run exercises active timers, fullscreen output and Paula sound. Its guest
dispatch/cycle/hash/PC signature and final picture match the previous locked-input
reference. All 3,330,048 queued audio frames were submitted and completed, with
device error 0. There were still 2112 reported audio gaps: delivery completion
does not establish continuous or improved sound.

Register restoration and cache witness checks pass, and owned memory is released.
The private player was removed afterward, Core1 is free, and installed normal/FPU
MD5 hashes remain unchanged.

## Sampled results

These estimates cover calls after frame 3000, extrapolated by 64 from measured
samples. They include timer overhead and are not exact totals or predicted FPS.

| Stage | Samples | Estimated time |
|---|---:|---:|
| Record-palette function, inclusive | 14,791 | 250 ms |
| Changed palette snapshot copy | 589 | 167 ms |
| Drawing-palette function, inclusive | 3,028 | 41 ms |
| Drawing palette copy | 12 | 3 ms |
| Five line-state clears | 14,763 | 644 ms |
| Empty timer scope | 14,791 | 18 ms |

The drawing-copy estimate has only 12 samples and is particularly uncertain.
The empty scope averages 6.21 timer ticks; the clear scope averages 227.36 ticks.
The total instrumented run takes 166.79 seconds, including boot and warm-up;
that whole-run interval must not be treated as the measured gameplay interval.

## Decision

Palette copies are not a substantial optimisation target in this Banshee test.
The core already reuses unchanged palettes. Removing changed snapshots risks
incorrect colours on earlier scanlines, HAM and Copper effects. Line clears cost
more, but this measurement alone does not justify removing required reset state.

Retain the existing build. No production change, FPS gain or audio improvement
is claimed. These findings apply to this workload, not every Copper-heavy demo.
Future work should prioritise the larger CPU/chipset costs already measured,
with matched gameplay output and audio checks before promoting a candidate.

[Evidence](palette-costs/) includes instrumentation patches, build/check scripts,
timer data, model states, the physical log and cleanup checks. No game or ROM
media is included.
