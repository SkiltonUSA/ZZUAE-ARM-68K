# Event-bounded JIT blocks and Cortex-A9 emitter tests

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

This experiment reduces overhead in the timing-correct JIT diagnostic. It does
not replace the installed player or change the 0.5.4 Beta release. The reference
is this port's 68020 interpreter, not cycle-exact 68000 bus emulation.

## Changes

1. Group up to 32 fixed-cost register/immediate instructions. Stop at memory,
   branch, privileged, exception or unknown operations. This gives the existing
   register allocator and backwards flag-liveness pass more useful work per
   dispatch, without moving device accesses across chipset events.
2. Record the group's guest cycle budget. If a warm group would cross the next
   chipset event, or an interrupt/trace/special condition is pending, execute one
   interpreter instruction instead. Cold traces advance events after each
   instruction and stop at the event boundary. Variable-cycle operations retain
   their runtime interpreter costs.
3. Return the cycle budget from the existing checksum-validation lookup. The
   first version looked up the same block twice; the second removes that work.
4. Test upstream A32 ARMv6T2 emitter paths on the Cortex-A9 separately. They use
   MOVW/MOVT, BFI/BFC and UBFX for constants and byte/word operations. The build
   remains ARM state, with guest FPU JIT and ARM integer-divide paths disabled.

The 32 MiB executable cache, 64 MiB allocation, 2 MiB active-metadata budget,
self-modifying-code validation and bounded cancellation remain in place. No
firmware, fixed physical allocation or device-memory shortcut was introduced.

The [Z3660-AMIX review](amiga-uae4arm-z3660-review.md) supports investigating
register reuse and servicing overhead. Its real-chipset architecture and CPU
performance claims do not predict ZZUAE's full-machine performance.

## Repeated hardware measurements

Two fresh-process runs per variant on the A4000TX/ZZ9000, XX19c/XACP1.7. All use
MAX with no live presentation/audio, identical media and volatile disk writes.
Frontier runs 3,000 guest frames; Alien Syndrome and Workbench 2.0 run 1,800.
Numbers are mean elapsed seconds and throughput change against the
instruction-sized MOVW/MOVT reference. They are not unique gameplay-frame FPS.

| Workload | Instruction-sized reference | Initial groups | One-lookup groups | Groups + A9 emitter | Combined change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frontier intro, A500/Kickstart 1.3 | 58.329744 | 57.774672 | 56.711029 | 56.757548 | +2.77% |
| Alien Syndrome startup, A1000/Kickstart 1.2 | 33.238049 | 33.935681 | 33.372936 | 32.912460 | +0.99% |
| Workbench 2.0 boot, A600/Kickstart 2.05 | 22.742149 | 23.105553 | 22.721285 | 22.622938 | +0.53% |

All 24 headless JIT runs and three interpreter controls completed with matching
final guest cycles, PC and frame hash for each workload, restored
register/MMU/cache witnesses, and released their memory.
The initial grouped version regressed Alien Syndrome and Workbench; removing
the duplicate lookup recovered most of that loss. The A9 emitter recovers Alien
Syndrome’s small regression and adds a modest Workbench gain; its Frontier result is slightly slower than one-lookup groups
alone. The one-lookup Workbench difference (+0.09%) is effectively unchanged.
Two runs are not a confidence interval.

A fresh interpreter control run in the same candidate payload completed each
workload with matching guest state:

| Workload | 68020 interpreter, one run | Combined JIT, two-run mean | JIT elapsed-time overhead |
| --- | ---: | ---: | ---: |
| Frontier | 47.466952 s | 56.757548 s | +19.57% |
| Alien Syndrome | 26.229475 s | 32.912460 s | +25.48% |
| Workbench 2.0 | 19.000368 s | 22.622938 s | +19.07% |

The timing-correct JIT remains slower in all three workloads. This is progress
against the previous diagnostic, not a general JIT speedup over interpretation.
The interpreter controls are single runs; they establish the size of the gap,
not a distribution of timings.

## Validation

Native tests cover exact event deadlines, insufficient budget, unsigned clock
wrap, pending interrupts/trace, permitted register operations and rejected
memory/control operations. A separate test executes the actual validation helper
with active, missing, invalidated and reclaimed blocks, checking that it uses one
lookup and returns only a validated cycle budget.

The actual ARM payload's CPU tests cover registers, CCR/X, memory, remapped I/O,
self-modifying code and generated code near the end of the 32 MiB cache. Synthetic
full-machine fixtures compare cycles, PC, registers/CCR, Chip RAM and pixels
against the interpreter for beam reads, variable branch costs, IRQs, metadata
pressure and maximum-sized groups. These instruction-model checks complement,
but do not substitute for, the physical runs.

The bitfield encoding test executes 23,760 BFI/BFC/UBFX cases at each of two code
addresses, including every valid field range, register aliasing and flag
preservation. The generated-code regression deliberately fails on the earlier
emitter when asked to require BFI/BFC execution. The CPU suite was expanded from
432 to 528 cases with byte arithmetic, logic, shifts and bit operations. Both
emitters passed all 528 cases at three load addresses with MMU protection. The
ARMv7 candidate executed 277 BFI/BFC and 38 UBFX instructions per address in that
suite. Model hooks counted 64,293 generated instructions in the old emitter and
63,348 in the candidate (-1.47%) for this synthetic workload. Those counts
exclude support/interpreter code and are not hardware speed measurements.
Cancellation, injected data-abort recovery and all five full-machine timing
fixtures also passed with the new emitter.

The UB helper tools were invoked for the new C++ helpers; they do not support
these files. No C++ coverage or mutation score is claimed.

## Live-run limitation

The one-lookup candidate's initial 6,000-frame Alien Syndrome window/AHI run hit
the harness's 150-second timeout. It displayed 1,151 frames, reported 1,979 audio
queue gaps and did not complete the requested workload. All submitted audio
bytes completed; the task stopped, the mouse handler was removed, registers/MMU
and cache witnesses were restored, and owned memory was released. This is a
failed completion test, not evidence of stable audio. The installed player,
launcher/preferences and saved screen mode were unchanged afterward.

The instruction-sized reference also timed out on the identical 6,000-frame
window/AHI workload at 150 seconds, displaying 1,112 frames and reporting 1,968
queue gaps. Its audio task, mouse handler, memory and MMU/cache state also cleaned
up. The long-run completion problem therefore predates event grouping; neither
run is a successful 6,000-frame benchmark. The timeout remains a diagnostic
limit, and was not enlarged to make this test pass.

The shorter 1,800-frame window/AHI comparison completed in both builds with
matching cycles/PC/frame hash. Reference: 41.420382 s; one-lookup groups:
41.380888 s. Displayed frame counts were 596 and 643 respectively; asynchronous
frame delivery makes these unsuitable for an exact frame-for-frame display
comparison. Both delivered 1,153,024 PCM bytes with no AHI task error. Both
reported queue gaps (244 and 228), and this startup segment's PCM was silent.
It therefore proves lifecycle/transfer completion, not audible-game quality.

The 3,000-frame active-audio pair also completed with matching guest cycles
`426278855`, PC `00017972` and frame hash `c03d0760`:

| Window/AHI run | Guest run time | Displayed frames | Nonzero PCM frames | AHI queue gaps |
| --- | ---: | ---: | ---: | ---: |
| Instruction-sized reference | 80.236404 s | 813 | 326,009 | 808 |
| Groups + A9 emitter | 78.633391 s | 880 | 326,009 | 799 |

Both delivered/completed 1,922,048 PCM bytes, stopped the audio task, removed the
mouse handler and restored/released all hardware state. This single pair is
about 2.04% faster, but neither run demonstrates gap-free audio. Audio was not
auditioned, and asynchronous presentation does not guarantee identical displayed
frames. The timing-correct diagnostic needs more work before normal play.

## Reproduction

```sh
python3 scripts/build_uae4arm_jit.py --event-blocks --cache-kib 32768 \
  --movw-constants --player --hardware
```

Add `--armv7-emitter` for the separate Cortex-A9 bitfield candidate. Build outputs
use distinct directories. No installed application is overwritten by either
command. [Raw model, build and hardware records](../amiga/records/2026-10-27/uae4arm/jit-events/).

## Next useful investigation

The remaining gap calls for profiling dispatch, checksum validation, fallback
and generated-code time separately. Extending blocks to RAM operations may help,
but needs runtime bank checks, exact cycle budgets and immediate exit before
side-effecting I/O. Learned totals remain unsuitable for variable-cost branches.
Keep the existing differential fixtures and hardware endpoint comparisons as
release gates. Larger caches, fixed interrupt polling intervals and a blanket
assembly rewrite do not address these correctness/performance tradeoffs.
