# ZZUAE: 32 MiB JIT cache and direct RAM experiment

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

The 32 MiB callback JIT cache improved repeated Alien Syndrome startup throughput
by **4.12%** on the A4000TX. The guarded direct RAM experiment was slower and
remains opt-in. These are experimental 68020 JIT results, not a change to the
compatible 68000 default.

## Memory and build contract

The larger software translation cache uses a **64 MiB Exec-owned ZZ9000 runtime
allocation**, increased from 32 MiB. It does not enlarge the Cortex-A9 hardware
cache or the emulated Amiga's RAM. The remaining allocation holds emulated
memory, core state, page tables, transport buffers and stack space.

`--cache-kib 32768` selects the larger cache. The linker, image packer, ARM
worker and 68K launcher use the same allocation size. The ordinary build still
uses 512 KiB, allowing a reproducible baseline. Compatible and FPU builds are
unchanged. No fixed physical DDR address or firmware modification is used.

The A32 branch range is checked rather than silently wrapping. Translation-cache
end limits reserve entry-stub space; generated code is tested at the first,
middle and final cache pages. Cache publication, private MMU mappings, teardown
and register restoration retain the existing XACP execution contract.

## Direct RAM approach

Generated code looks up the current UAE memory bank for every access. Only the
exact Chip RAM and Slow RAM bank objects qualify. It uses the current start
address, mirror mask, allocation length and native buffer pointer. Aligned byte,
word and long accesses within that allocation use ARM loads/stores with
big-endian conversion.

ROM, hardware registers, unfamiliar banks, unaligned accesses and accesses
extending beyond the allocation retain callbacks. Indirect PC translation,
self-modifying-code checks, trace limits and event servicing are unchanged.
The experiment retains the callback ABI register spill. Its extra guards and
code size can outweigh the saved call; these results do not establish that all
direct-memory designs would be slower.

## Repeated Alien Syndrome measurements

Two runs per build: 1,800 emulated frames, A1000 profile, Kickstart 1.2, expanded
RAM, 68020 JIT, temporary disk writes, identical timed mouse input, MAX frame
setting, no live window or audio. FPS is emulated frames divided by elapsed
boot/run time. It includes startup and title activity, **not gameplay-drawn FPS**.

| Memory access | JIT cache | Mean time | Emulated FPS | Versus baseline |
|---|---:|---:|---:|---:|
| Callback baseline | 512 KiB | 27.213 s | 66.14 | — |
| Guarded direct RAM | 512 KiB | 27.920 s | 64.47 | −2.53% |
| Callback | 32 MiB | 26.137 s | 68.87 | **+4.12%** |
| Guarded direct RAM | 32 MiB | 26.432 s | 68.10 | +2.95% |

Direct RAM is still 1.12% slower than callbacks with the same 32 MiB cache.
Callback translation-site counts fell from 35,791 to 13,002, consistent with
less recompilation. These are compile-site counters, not instruction or cache
miss counters. Final picture hash and PC matched across all eight runs; guest
cycle totals differed by up to five cycles at the frame boundary. This is not
an exact-state differential proof.

## Frontier and live audio follow-up

Frontier intro: 3,600 emulated frames, A500 profile, Kickstart 1.3, expanded RAM,
temporary disk writes, MAX, no live window/audio.

| Build | Run time | Emulated FPS | Final PC / picture hash |
|---|---:|---:|---|
| Callback512 | 63.009 s | 57.13 | `00c31146` / `7ab688c0` |
| Callback512 repeat | 62.995 s | 57.15 | `00c31146` / `7ab688c0` |
| Callback32 | 58.957 s | 61.06 | `00c3b754` / `c0f7d940` |
| Direct32 | 59.843 s | 60.16 | `00c3b754` / `c0f7d940` |

Both baseline runs reproduced the same final state. The two larger-cache builds
also agree with each other, but differ from the baseline. Guest-cycle totals
also differ by 193 cycles. This result is **not an exact-state performance
comparison**; a later [timing investigation](amiga-uae4arm-jit-timing.md) reproduced
the causes and matched the interpreter with both cache sizes in an isolated,
slower diagnostic mode. The ordinary JIT results above are unchanged. Keep the JIT experimental. These numbers do not measure Frontier's
internally drawn 3D frame rate.

A separate 3,600-frame Alien Syndrome live-window/AHI comparison used a 25 FPS
presentation cap and the same timed input:

| Metric | Callback512 | Callback32 |
|---|---:|---:|
| Run time | 77.543 s | 77.522 s |
| Completed display presentations | 1,161 | 1,265 |
| Deferred presentations for audio reserve | 639 | 535 |
| Audio queued / submitted / completed | 2,307,072 each | 2,307,072 each |
| Audio late-queue observations | 451 | 443 |
| Device errors | 0 | 0 |

The larger cache allowed more display updates within nearly the same run time.
Final picture and PC match, but guest cycles and nonzero PCM-frame counts differ;
this is not a bit-exact audio comparison. All data was delivered and both runs
cleaned up successfully. Late-queue observations remain substantial and audible
quality has not been checked by listening. No claim of resolved audio stability.

## Correctness checks

- Expanded interpreter differential fixture: 432 comparisons at three modeled
  addresses for both large-cache variants. Cases cover Chip/Slow RAM, odd
  addresses, ROM, unmapped memory, 64 KiB boundaries, 24-bit aliases and changing
  a translated block's data bank from RAM to a device without invalidating it.
- Warmed aligned RAM accesses bypass callbacks in the direct-path model; device
  accesses retain side effects. Actual guest blocks execute near the far end of
  the 32 MiB cache.
- Synthetic whole-machine comparison matches CPU/CCR, RAM, pixels, PCM, cycles
  and frames between interpreter, direct512, callback32 and direct32. Dispatch
  counts are excluded because compilation changes them.
- Executable-arena tests cover publication, rewrite, full capacity, invalid
  spans, release/reallocation and execute-never restoration. Cancellation and
  injected-fault recovery pass in the instruction model.
- Native 64 MiB MMU-plan test covers all 16,384 allocation alignments. The image
  packer rejects an undersized allocation, unsupported size and stack overlap.
- Physical CPU diagnostic passes all 432 comparisons. The 64 MiB runtime passes
  mapping validation and 51 generated-code publication/execution checks,
  including the first, middle and final arena locations. Register/MMU/cache
  witnesses restore cleanly and owned memory is released.

Model checks do not replace physical execution; neither establishes every game
is compatible with the experimental JIT.

## Installed development build

The tested callback32 executable was installed as `ZZUAE-JIT` on the A4000TX,
CRC32 `3DE6BAFE`, with the previous 512 KiB build retained for rollback. Select
**68020 JIT (experimental)** in the launcher to use it. The compatible engine
remains the default. The launcher, compatible/FPU players, saved configuration
and Workbench display preferences were unchanged; FinalWriter remained open.

The public 0.5.4 Beta download has not been replaced by this experiment. Source,
measurements and build commands are backed up here; the 32 MiB executable is a
local development installation.

## Reproduce

```sh
# Callback baseline
python3 scripts/build_uae4arm_jit.py --player --hardware
# Larger callback cache
python3 scripts/build_uae4arm_jit.py --cache-kib 32768 --player --hardware
# Isolated direct RAM candidate
python3 scripts/build_uae4arm_jit.py --direct-ram --cache-kib 32768 --player --hardware
# CPU diagnostic
python3 scripts/build_uae4arm_jit.py --direct-ram --cache-kib 32768 --hardware
```

Outputs are isolated under `.context/amiga/uae4arm/jit-execution`,
`jit-execution-32768` and `jit-direct-32768`. Build scripts do not install or run
Amiga executables. The report's source/model/physical logs and artifact hashes
are in [the evidence directory](../amiga/records/2026-10-27/uae4arm/direct-ram/).
