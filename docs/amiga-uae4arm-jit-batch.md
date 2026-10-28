# Combined JIT optimisations and exception batching — 0.5.5 Beta

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

This update combines the register-group and drawing/audio-pressure candidates,
then measures one further change: reuse the guest exception context across a
bounded accelerated-dispatch call. Compatible 68000 remains the default.

## Implementation

The optional `--batch-context` build keeps one `setjmp` context for a dispatch
batch instead of setting one up for every translated block or fallback
instruction. The caller still bounds each batch to 256 dispatches. Every normal
dispatch retains its original interrupt, special-service and frame-limit checks.
A fault restores the enclosing context, services the bus exception, accounts
that dispatch exactly once, then starts a new bounded context. The cycle origin
is volatile because it must survive `longjmp`.

There is no interrupt-check decimation, change to the guest clock, direct-RAM
bypass or new firmware dependency. The experimental core retains event-bounded
traces, MOVW/MOVT constants, ARMv7 bitfields, the precomputed cycle map and the
32 MiB executable cache inside a 64 MiB Exec-owned runtime allocation.

The optional VFP-backed FPU player is rebuilt against the same core and flags.
Its `--base` build argument selects that recorded build, preventing an accidental
return to the earlier cache/timing configuration. Product versions must match.

## Validation

- Native dispatcher/reference tests: 800 cases including opcode, validation and
  interrupt faults, nested bus faults, halt/frame limits and counter wrap. UBSan
  passes. A fault-free 256-dispatch call uses one context instead of 256.
- Python source-transform mutation tests: 4/4 selected mutations killed. These
  tools do not measure C++ mutation coverage.
- Both candidate ARM binaries: 528 CPU comparisons at three runtime addresses,
  including execution near the cache end; cancellation and injected fault checks.
- Six timing fixtures compare cycles, CPU registers/CCR, Chip RAM and pixels.
- Combined and batched 12-frame audio-pressure fixtures produce identical CPU,
  RAM, pixels and PCM hashes; input and pressure refresh checks pass.
- The lifecycle harness now handles the complete 64 MiB allocation and verifies
  restoration across the entire page-table span. Success, cancellation, invalid
  options, cleanup abort, rejected vectors and unlimited cancellation pass.

## Repeated headless measurements

Two fresh processes per candidate and workload, without presentation or audio.
The second round reversed candidate order. Values are mean elapsed times;
throughput gain is combined-time / batched-time minus one.

| Workload | Combined | Plus batching | Throughput gain |
| --- | ---: | ---: | ---: |
| Frontier, 3,000 guest frames | 54.462773 s | 52.113478 s | +4.51% |
| Alien Syndrome, 1,800 guest frames | 31.050527 s | 29.670724 s | +4.65% |
| A600 / Workbench 2.0, 1,800 guest frames | 22.060735 s | 21.245780 s | +3.84% |

Each pair preserves guest cycles, final PC, frame count and framebuffer hash.
Register/MMU/cache witnesses and owned-memory release pass in all 12 runs.
These modest sample counts do not establish a statistical confidence interval.

## Windowed audio measurement

Alien Syndrome, 3,000 guest frames, windowed direct display, 30 FPS display
selection, AHI 32 kHz stereo. One fresh process per candidate:

| Build | Elapsed | Draws/presentations | Late AHI submissions |
| --- | ---: | ---: | ---: |
| Earlier precomputed-map baseline | 75.953433 s | 3,000 / 954 | 782 |
| Register groups + early drawing/pressure | 72.170081 s | 1,085 / 1,085 | 685 |
| Combined build + exception batching | 69.988656 s | 1,192 / 1,192 | 586 |

The combined candidate is **5.24%** faster than the earlier baseline. Batching
adds **3.12%** over that combination, for **8.52%** total throughput improvement
against the earlier baseline. These are ratios of measured elapsed times;
separate optimisation percentages were not added together.

All three runs have matching guest cycles, final PC/framebuffer and nonzero-PCM
counts. Each queues, submits and completes 1,922,048 PCM frames. Backend errors,
input overflows and display failures are zero. The batched candidate presents
more frames while doing less exception-context work. Roughly 60 seconds of PCM
still takes about 70 seconds to produce: sustained real-time audio is unresolved.

## Build

```sh
python3 scripts/build_uae4arm_jit.py --event-blocks --cache-kib 32768 \
  --movw-constants --armv7-emitter --flat-cycles --early-draw \
  --early-pressure --register-groups --batch-context --player --hardware
```

Omit `--batch-context` to reproduce the combined comparison build. Pass the
chosen output directory to `build_uae4arm_fpu.py --base DIRECTORY --hardware`.
Build the compatible player and launcher normally; all product binaries use
`0.5.5-dev`. The signed offline AmiPkg installer and manual ZIP share one payload.

## Packaged players on hardware

The FPU hardware self-test passes arithmetic, square root, rounding and extended
storage checks with zero ARM FP-state mismatches. The packaged FPU player also
boots A600 / Kickstart 2.05 / Workbench 2.0 for 1,800 frames and restores all
register/MMU/cache state. This is a compatibility smoke test, not an FPU game
speed claim.

The packaged compatible player completes a 300-frame Alien Syndrome window/AHI
run, drains all queued PCM and removes its input handler. All three final checks
release their owned allocation. The pre-DF1 JIT package was byte-identical to the batched
binary used for the 3,000-frame window/audio measurement and repeated headless
comparisons above.

## Installer validation

The final signed AmiPkg package was installed into a fresh RAM drawer on the
physical Amiga. Dependency/signature checks passed and all 18 payload files
matched local CRCs. Reinstalling the same package retained test settings and
media files. Existing system scanline tools were preserved. The manual ZIP and
installer payload also pass byte-for-byte equivalence, SHA-256 and signature
corruption tests on the Mac.

The production drawer was then upgraded with rollback copies retained. Its
18 installed files match the package; the 0.5.5-dev launcher opens. Saved app
settings, Workbench display preferences and the existing FinalWriter session
are unchanged. ARexx confirms Core1 is idle after testing.

## Limits

Timing measurements count a fixed number of guest frames, not unique game
animation frames. Late AHI submissions are observations, not audible-gap
measurements. The earlier 6,000-frame live test timed out at its unchanged
150-second deadline. This release does not claim that long-run audio gate or
listening acceptance passed. JIT and FPU remain optional experimental modes;
compatible 68000 is unchanged as the normal default.
