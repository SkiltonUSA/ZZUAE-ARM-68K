# ZZUAE 0.5.4 development: audio, NEON and A600 compatibility

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

This follow-up keeps the 68000 interpreter and original OCS/ECS guest timing.
The normal build does not enable guest JIT. The published 0.5.3 release is
unchanged; the new code is a development build.

## Renderer and audio changes

Four specialised NEON loops select brightness and P96 byte order once per row.
Full-brightness rows skip multiplications; alpha is calculated once per row.
All previously touched D registers are still preserved, with the existing
per-frame state witness. Smaller windows and disabled SIMD use scalar fallback.
This reduces conversion work without changing the number of RTG bytes written.

The host copies a bounded snapshot of queued PCM before servicing graphics.
It publishes the local batch after copying and signals the audio process once.
Both queue counters remain wrap-safe; the consumer cannot see partially copied
blocks. A four-block prebuffer experiment showed no benefit in the tested run,
so the normal two-block prebuffer (about 64 ms at 32 kHz) is retained. AHI links,
Paula channel ownership, sample rate and PCM data remain unchanged.

## Matched physical results

A4000TX/ZZ9000, A1000 profile, 512 KiB Chip, Kickstart 33.166, Alien Syndrome,
640 × 480 Direct window, private temporary disk writes, scripted title input.
FinalWriter remained open; no screenshots or injected input during measured runs.
These are startup/title throughput measurements, not sustained gameplay FPS.

| 1,800 guest frames, audio Off / MAX | 0.5.3 | Revised NEON | Throughput gain |
|---|---:|---:|---:|
| Scanlines Off | 36.401 s / 49.45 FPS | 34.590 s / 52.04 FPS | 5.24% |
| Soft scanlines | 36.453 s / 49.38 FPS | 34.612 s / 52.01 FPS | 5.32% |

All four runs matched guest instructions (8,458,518), cycles (106,505,156),
final PC (`fc0cd0`) and native frame hash (`73022f00`). Each setting has one
paired run; these are not confidence intervals or a universal speedup.
They compare against the NEON-enabled 0.5.3 build, not the older scalar baseline.

| 3,000 guest frames, AHI / 25 display FPS / Soft | Elapsed | Late queue observations |
|---|---:|---:|
| 0.5.3 | 60.675 s | 36 |
| Revised NEON, unchanged host audio | 60.322 s | 0 |
| Revised NEON + batches + experimental four-block prebuffer | 60.340 s | 0 |

These three runs matched guest state and all 1,923,072 queued PCM frames were
submitted/completed without device errors, with 203,363 nonzero frames. Audio
pacing intentionally holds guest time near PAL rate: rendering headroom improves
queue delivery rather than accelerating sound. The four-block prebuffer added
no demonstrated benefit and was reverted. A queue observation is not a measured
dropout duration; zero observations do not replace listening acceptance.

## A600 and Workbench 2.0

The supplied Workbench disk identifies itself as 37.67. Both Kickstart 2.05
revisions passed physical desktop boots: 37.350 with 1 MiB Chip RAM, and 37.300
with 2 MiB. Each completed 1,800 guest frames and clean restoration/release.
The existing private LoadWB/EndCLI startup copy was used. This is desktop boot
compatibility, not proof of every application or the complete original startup.
No media, display preferences or firmware were modified.

## JIT prerequisite: executable memory and cache publication

The experimental build reserves a private arena within the existing Exec-owned
32 MiB allocation. It validates every page descriptor before enabling execution,
uses local A9 DCCMVAU/ICIMVAU publication with barriers and branch-predictor
invalidation, and restores XN on release. It does not use Linux mmap, fixed
unowned DDR addresses, global L2 maintenance or a different Core1 lifecycle.

The physical cache witness passed **48 generated/rewritten ARM calls**, including
L1-line and page crossings, plus release/reallocation and clean MMU/cache/register
restoration. Model checks cover two allocation alignments, maximum capacity,
invalid spans, invalid frees and rejection before partial mapping changes.
The model does not simulate real hardware cache coherence; the physical result
is recorded separately.

These are real cache hooks and ARM code execution, **not emulated 68K JIT**.
The relocatable link of upstream compemu, compstbl and support code against
the implemented hooks passed. It uses a 512 KiB JIT cache instead of upstream's
16 MiB default; remaining CPU-dispatch symbols are intentionally unresolved. The isolated port
also removes signed-shift undefined behaviour from the ARM immediate encoder;
all 4,096 rotated-immediate patterns passed signed/unsigned UBSan tests. Remaining work includes compatible CPU tables/dispatch,
bounded block execution and chipset events, FP/SIMD context and exception
handling, self-modifying guest code, differential tests and hardware validation.
Current 68000 profiles remain unchanged. No JIT option is exposed in the launcher.

## Validation

Actual ARM leaf tests cover the full RGB565 colour space, both P96 byte orders,
all supported brightness levels, buffer guards and SIMD/integer state preservation.
Direct-display tests cover scaling, snapshots, mapping/grant/ACK ownership and
cancellation. Synthetic stereo DMA tests produced identical CPU, Chip RAM,
frame and PCM results for baseline and candidate. The pressure test drains the
final published PCM block before hashing, so polling cadence cannot change
which final block is included in the report. Native ASan/UBSan tests cover
the actual host batch function. Shared framework tests passed.

## Longer audio workload

A 6,000-frame AHI/Soft run of the NEON/batched candidate (two-block prebuffer)
exposed a heavier part of the title/music sequence: 123.610 s, 3,845,120 PCM
frames completed, 2,124,129 nonzero frames, and 411 late queue observations.
There were no device, SIMD, display or teardown errors, but the shorter run's
zero-gap result did not generalise. This motivated an audio-reserve-aware
presentation experiment: defer display delivery when queued PCM is low while
continuing guest CPU/chipset/sound emulation and input. The first display is
always delivered and no more than three scheduled presentations may be deferred
consecutively. This trades some display updates for audio headroom; it does not
skip guest CPU or audio samples.


The adaptive candidate completed the same 6,000 guest frames in **120.422 s**,
with **1** late queue observation (versus **411**), identical guest instructions,
cycles, PC, frame hash and PCM counts. All 3,845,120 PCM frames completed without
device errors. It delivered **2,549** display updates and deferred **451/3,000**
(15.0%); average presentation was about **21.2 FPS** against the selected 25 FPS
ceiling. This is a display/audio trade-off, not a free rendering speedup. Guest
throughput was 49.82 FPS, with no dropped CPU execution or PCM samples.

The accepted build retains this bounded audio-reserve policy with the original
two-block prebuffer. There is still one queue observation, and real listening
acceptance remains pending. Every SIMD-state, mapping, restoration and owned-memory
release check passed. This is one matched long pair on one game sequence.


Paula direct's device path and F9 Smooth/Hard/Off cycling passed a separate F10
cancellation check (479,232 silent intro PCM frames, one late queue observation). Audio drained, the window closed, SIMD state matched and
all MMU/cache/register restoration and memory-release checks passed. This tests
device lifecycle and controls, not listening quality.

Evidence: `amiga/records/2026-10-27/uae4arm/followup054/`, including matched logs,
model reports, build manifests, JIT-link audit and A600 desktop captures.


## Installed development version

The matched 0.5.4-dev launcher/player were CRC-verified and installed, retaining
0.5.3 executables for rollback. Preferences and media were preserved. The normal
build has NEON and audio-reserve presentation enabled; stage profiling and the
JIT cache witness are disabled. The launcher was reopened with FinalWriter's
unsaved document intact. The public 0.5.3 release package is unchanged.

The installed player also passed a 300-frame AHI/Smooth smoke run: 191,488
PCM frames completed, 148 display updates, two deferred updates, one late queue
observation and zero device/SIMD errors. Full restoration and memory release
passed. Its intro PCM was silent; this is an installation/lifecycle check.
