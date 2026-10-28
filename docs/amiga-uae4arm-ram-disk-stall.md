# Background RAM-disk usage-query stalls

## Result

Rick Dangerous periodically paused in both windowed and fullscreen play, with
Paula sound. Removing obsolete development files from the Amiga RAM disk removed
the recurring long stalls in the measured repeats. The gameplay check then
confirmed the fix. Frontier and State of the Art were also reported to run
noticeably faster after cleanup; these are qualitative observations, not new FPS
measurements.

This was a host scheduling problem exposed by background RAM-disk queries.
It did not require an emulator, game-disk, firmware or audio-driver patch.
**0.5.6 Beta documents the remedy; installation does not automatically clean RAM:.**

## What happened

Temporary player builds and installer trials had accumulated on RAM:. A native
`Info()` query took **342–356 ms** with approximately **296 MiB** in use. A vertical
blank task sampler recorded the RAM handler running at priority 10 for about
20 consecutive 60 Hz samples, recurring every 320 samples (about 5.3 seconds).
The lower-priority host player consequently could not service presentation and
audio promptly. Core1 continuing to run does not remove this host dependency.
The application issuing the periodic query was not identified.

After preserving test results and deleting only the known obsolete staging
files, RAM-disk usage fell to approximately **23 MiB** and `Info()` took
**24–29 ms**. Installed applications, ROMs, disks, saves and preferences were
preserved. Player and disk checksums remained unchanged.

## Measurements

Rick Dangerous 1, compatible A500 profile, Kickstart 1.3, 512 KiB Chip plus
512 KiB expansion RAM, Paula audio and a 50 FPS display limit. Each controlled
run processed 1,800 guest frames. A diagnostic host recorded completion times
in memory and printed them after the run; no bridge requests or screenshots
were taken during measurement.

| Measurement | Before cleanup | After cleanup |
|---|---:|---:|
| Windowed completion gaps over 100 ms | 7 | 0 |
| Fullscreen completion gaps over 100 ms | 7 | 0 |
| Largest windowed gap | approximately 387 ms | 87.595 ms |
| Largest fullscreen gap | approximately 388 ms | 79.463 ms |
| RAM-disk `Info()` duration | 342–356 ms | 24–29 ms |

These are **host frame-completion gaps**, not unique game-frame FPS or a guarantee
of perfectly even display scanout. Smaller timing variations remain. Both repeat
runs completed all 998,400 queued PCM samples with no device error, restored
register/MMU/cache state and released the application allocation. One late audio
submission was still recorded in each repeat. This does not resolve the separate
experimental JIT/AHI long-run audio limitations documented elsewhere.

Rick Dangerous 2 also exhibited the host gaps in instrumentation, although the
original visual report concerned only Rick Dangerous 1. An independent native
68K timer observed long delays without any emulator running.

The stalls persisted with progress logging disabled, bridge TCP disconnected,
NewMeter closed, USB CD/DVD unplugged and emulated audio disabled. Raising only
the player's priority did not solve the problem and was not retained. An initial
run with screenshots/polling was excluded because those operations disturbed
timing.

## Effect on earlier benchmarks

Earlier physical tests did not consistently record RAM-disk occupancy or the
cost of background usage queries. Their elapsed times, presentation rates and
audio-gap counts may therefore include this host interference. Treat previously
published hardware performance figures and percentage gains as **historical
results requiring controlled remeasurement**, not clean estimates of the effect
of an individual optimisation. This is especially important for small gains.
It is not established that every historical run was affected, or by how much;
do not subtract a fixed pause penalty or apply a correction factor.

Instruction-model results, guest-state comparisons and verified cleanup checks
remain evidence for their respective correctness claims. They do not establish
physical performance. Prior audio gaps/timeouts should be revisited under clean
conditions, rather than assumed resolved by this finding.

Repeat matched A/B runs with a documented RAM-disk baseline, the same background
applications and game sequence, no bridge polling during timing, and checks for
host stalls, audio delivery and clean shutdown. Do not combine earlier timings
with post-cleanup timings into a new percentage gain.

## Avoiding recurrence

- Keep completed builds and installer archives on disk, rather than accumulating
  them on RAM: during long development sessions.
- Archive needed results, close the test process, then remove only its known
  temporary staging files. Leave files still in use alone.
- If periodic pauses return, inspect RAM-disk contents and background usage
  queries before changing emulator timing or task priorities.
- Do not indiscriminately clear RAM:, ENV, T or Clipboards; they may contain
  active application data and unsaved work.

The installer performs no broad cleanup and makes no task-priority changes.
The release rebuild changes product version identification and documentation;
emulation, audio, JIT and scheduling algorithms remain those of 0.5.5.

Selected measurements and diagnostic sources are in
[the investigation record](../amiga/records/2026-10-28/uae4arm/ram-disk-stall/).

## Remaining scene-specific slowdown

After confirming the general improvement, the user supplied a short clip and
photos of State of the Art slowing during the black-dancer silhouette over a
shifting coloured tile background. That specific slowdown remains unresolved.
The capture identifies the scene; it is not a measured guest FPS benchmark.

The pinned UAE core records colour-register changes and `do_color_changes()`
renders scanline spans between those changes. Copper activity and fragmented
colour-span drawing are plausible profiling targets, alongside guest CPU,
Blitter work, presentation and audio waiting. The footage does not establish
which dominates. The host CPU meter is not an A9 utilisation measurement.
Reproduce this scene with clean RAM staging and per-stage counters before
changing Copper timing or claiming a rendering optimisation.

## Release verification

All eight packaged executables in 0.5.6 match the 0.5.5 binaries byte for byte
after substituting the product version string. ZIP/AmiPkg payload equivalence,
signature verification, corruption rejection, member hashes, dependency checks
and private-media exclusion pass. The new version therefore retains the tested
executable code; these packaging checks are not another physical timing run.
