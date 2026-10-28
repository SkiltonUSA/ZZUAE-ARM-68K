# ZZUAE 0.5.3-dev — NEON renderer and optimisation experiments

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

The new renderer uses a guarded integer NEON leaf for 640-pixel RGB565 rows.
It preserves the compatible 68000, OCS/ECS timing and the 32 MiB runtime allocation.
JIT and guest FPU emulation remain disabled. No firmware change is required.

## Measured hardware results

A4000TX/ZZ9000, A1000 with 512 KiB Chip RAM, Kickstart 1.2, Alien Syndrome,
Direct 640 × 480 Workbench window and temporary disk writes. FinalWriter remained
open. The first four rows use audio Off and uncapped presentation; these are
startup/title-sequence measurements, not gameplay FPS or full-game compatibility.

| Renderer | Software scanlines | Guest frames | Seconds | Emulated FPS |
|---|---|---:|---:|---:|
| 0.5.2 scalar | Off | 1,800 | 39.983 | 45.02 |
| NEON | Off | 1,800 | 36.529 / 36.363 | 49.28 / 49.50 |
| 0.5.2 scalar | Soft | 1,800 | 42.230 | 42.62 |
| NEON | Soft | 1,800 | 36.378 | 49.48 |

Off improved **9.7%** using the mean of the two NEON runs; Soft improved **16.1%**.
All five runs matched 8,440,230 guest instructions, 106,255,092 guest cycles,
final PC `fc0cd0` and native RGB565 frame hash `73022f00`. Pixel equivalence of
the presented image is checked separately by the ARM model.

With AHI, Soft scanlines and a 25 FPS presentation cap, the 3,000-guest-frame
music/title sequence improved from **63.239 to 60.602 seconds**. Both runs
completed 1,922,048 PCM frames, including 202,339 nonzero frames, without a device
error. Queue-gap observations fell from **334 to 34**. This counter records late
queue observations, not the duration of audible dropouts. Listening acceptance
remains pending. The guest state, cycles and final frame hash matched again.
A framework smoke check occurred during the baseline audio run; no screenshots
or input injection occurred in either audio comparison.

## Implementation and state handling

`convert_neon.S` expands eight RGB565 pixels at a time, applies integer brightness
and interleaves the four destination bytes. Both P96 byte orders and the existing
alpha-byte dimming are preserved. The converted row stays in private cached RAM;
the existing scalar writes deliver it to the granted RTG bitmap. This does not
reduce the number of bitmap bytes written or alter display ownership.

The runtime checks CPACR, FPEXC and the SIMD feature registers without changing
firmware policy. A smaller window or unavailable NEON selects the scalar path.
Black rows retain the existing zero-fill path. Every register touched by the
assembly leaf is saved/restored. It does not call other code, throw or yield;
no SIMD state spans the integer-only CPU setjmp/longjmp boundary. The frame
wrapper also compares all 32 D registers and FPSCR before and after conversion.
The build audit permits SIMD only in the named assembly routines and still
rejects compiler-generated FP/SIMD and unsupported A9 integer divide instructions.

## Validation

- ARM instruction execution over the RGB565 colour space, both byte orders,
  all brightness levels, source/destination guards and buffers not aligned to 16 bytes.
- D0–D31, FPSCR, stack and integer callee registers preserved; disabled feature policy detected.
- Full direct-display model with NEON enabled and disabled: 640 × 480,
  552 × 414 and 320 × 240, all scanline modes, held-frame capture, nonce failure,
  mapping collision, cancellation, grant/ACK ordering and mapping removal.
- Synthetic stereo DMA baseline/candidate comparison: identical PCM hash, CPU/CCR,
  Chip RAM, frame hash and guest counters.
- Physical smoke and measured runs: no SIMD mismatches, register/MMU/cache witness
  restoration passed, and application memory released. The longer audio run
  performed 1,500 SIMD checks while delivering 3,000 guest frames.
- `make test-amiga-arm test-amiga` passed. Model results do not establish physical
  cache performance or audible quality.

## What the profile says

An optional instrumented build timed the 3,000-frame AHI sequence in 60.668 s.
Timers include waits; these figures are not pure CPU utilisation. Scopes are
nested: drawing includes presentation and bitplane conversion; presentation
includes direct conversion; audio updates include PCM publication.

| Timed stage | Inclusive seconds |
|---|---:|
| Drawing, including presentation | 13.976 |
| Bitplane conversion (inside drawing) | 1.228 |
| Direct pixel conversion, mapping and bitmap stores | 5.776 |
| Presentation including direct conversion and waits | 9.524 |
| Audio update including publication | 7.836 |
| PCM publication including queue wait | 6.390 |

Subtracting nested scopes gives approximately **4.45 s** of drawing outside
presentation, **3.75 s** of presentation outside conversion, and **1.45 s** of
audio update outside publication. Bitplane conversion is about **2%** of this
sequence. Replacing every mixer or bitplane routine with SIMD therefore has
limited upside here. The unaccounted time includes CPU/chipset work and other
runtime paths; it must not be labelled entirely as CPU instruction execution.
Audio queue waits also include intentional guest pacing, so eliminating them
would not be a valid speed improvement.

The current mixer uses integer arithmetic. VFP is not enabled globally and no
standalone VFP speedup is claimed. Hardware floating point is more relevant to
the separate JIT divide/FPU work than this mixer.

## JIT audit — compiled components, not working guest JIT

The pinned UAE4ARM code selects JIT for an emulated 68020 or higher, while the
current profiles use the compatible 68000 interpreter. The code generator and
translation tables compile for Cortex-A9. The support layer initially failed on
Linux `MAP_ANON` and a Newlib `_B` macro collision. In an isolated source copy,
renaming the conflicting enum and replacing Linux allocation/cache operations
with **unimplemented platform declarations** lets the support unit compile too.
The required symbols remain unresolved deliberately; this is not a runnable JIT.

The next porting steps are:

1. Application-owned executable cache allocation, correct mappings, cache-line
   publication/barriers and full teardown using the existing XACP allocation.
2. A separate 68020 interpreter/table and CPU execution loop, plus bounded JIT
   block execution that still polls cancellation and services chipset events.
3. FP/SIMD preservation and exception handling across generated code. Cortex-A9
   lacks hardware integer divide; this JIT emits VFP sequences for some integer
   divides even with guest FPU disabled. The current leaf-only contract is insufficient.
4. Model differential tests for flags, divide, exceptions, self-modifying code
   and timing, followed by isolated physical runs before exposing a launcher option.

No Linux system call, mmap substitute or untested JIT code was executed on the
Amiga. The existing 68000 mode remains the compatibility baseline.

## Reproduce and evidence

Normal build: `python3 scripts/build_uae4arm.py`, then
`python3 scripts/build_uae4arm_machine.py --hardware`. Use `--scalar-renderer`
on the second command to build a reference without NEON. For diagnostic timings,
add `--profile-stages` to the first command; rebuild without it for normal use.

`tests/amiga/uae4arm/neon_row.py` tests the actual leaf instructions;
`check_machine.py ... --direct-test --neon` exercises the NEON display path.
`probe_uae4arm_jit.py` performs only the isolated compilation audit.
Records: `amiga/records/2026-10-27/uae4arm/neon/`.
The 0.5.3 Development Beta packages the guarded NEON renderer with profiling
disabled. JIT remains an isolated compilation experiment and is not enabled.

## Installed development build

The matched 0.5.3-dev launcher/player are installed on the development Amiga,
with profiling disabled and the 0.5.2 executables retained for rollback. A
300-frame AHI/Hard run passed with 150 state checks and one audio queue gap.
F9 Smooth/Hard/Off switching and F10 cancellation passed with 1,103 displayed
frames, no SIMD mismatches, clean restoration and memory release. The launcher
was reopened idle; preferences and firmware were not changed.
