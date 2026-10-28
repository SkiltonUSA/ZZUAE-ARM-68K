# JIT profiling, cache lists and opcode classification

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

Resolving opcode cycle-classification aliases once improved corrected-JIT
throughput by **4.24–4.30%** on three hardware workloads. A separate cache-list
shortcut produced no useful gain. The corrected JIT remains slower than the
matching 68020 interpreter. These experiments use the
32 MiB cache, event-bounded register groups and A32 bitfield emitter from the
[previous experiment](amiga-uae4arm-jit-events.md).

## Sampled timing

`--jit-profile` creates a separate build. A deterministic xorshift sampler
selects approximately one dispatch in 256 and measures five non-overlapping
intervals with the ZZ9000's existing ARM global timer. Counters remain private
to Core1 until the run finishes; the host then reads a bounded big-endian report.
Ordinary builds omit the instrumentation.

The intervals include timer-read cost, and sampling can miss expensive cold
compilations. Counter accumulation is excluded from the following interval.
These are diagnostic elapsed-time samples, not calibrated instruction-cycle
counts or precise CPU-utilisation percentages. An individual interval must be
shorter than the low timer word's wrap period (about 12.9 seconds here).

| Sampled interval | Frontier | Alien Syndrome | A600 Workbench 2.0 |
| --- | ---: | ---: | ---: |
| Dispatch/bookkeeping | 13.89% | 15.88% | 12.43% |
| Block validation | 9.01% | 13.26% | 4.88% |
| Handler, including cold learning | 17.98% | 26.98% | 19.39% |
| Interpreter fallback | 14.21% | 16.66% | 10.86% |
| Interrupt/special-state service | 44.91% | 27.23% | 52.44% |

Handler time includes interpreted cold traces, generated code and guest-cycle
callbacks. Interpreter fallback also includes cycle/event callbacks. Special
service includes Copper processing and the guest STOP loop; it is not purely
interrupt-polling overhead. Consequently, the table does not justify skipping
interrupt checks or copying AMIX's service cadence.

The profiler itself changes total runtime:

| Workload | Uninstrumented | Profiled | Instrumentation overhead |
| --- | ---: | ---: | ---: |
| Frontier, 3,000 guest frames | 56.737751 s | 57.907288 s | +2.06% |
| Alien Syndrome, 1,800 guest frames | 32.941123 s | 33.990623 s | +3.19% |
| Workbench 2.0, 1,800 guest frames | 22.635783 s | 23.330527 s | +3.07% |

These are one fresh-process hardware run per row/variant, with no live display
or audio. All final guest cycles, PC and frame hashes match the established
reference, with clean MMU/cache/register restoration and memory release.
Optimisation comparisons must use uninstrumented builds.

## Candidate: avoid redundant cache-list promotion

Validation accounts for enough sampled time to justify a small management
change. Upstream `raise_in_cl_list()` unlinks and reinserts a block even when
it is already the first entry in its cache bucket. The `--cache-head` candidate
recognises that case and leaves the links alone. It still refreshes the selected
handler, because checksum invalidation can change that handler without moving
the block. Non-head entries retain the existing promotion path.

Checksum calculation, dependency validation, invalidation, cache reclamation,
event budgets and guest execution are unchanged. The change introduces no RAM
shortcut or delayed interrupt handling. Two fresh-process runs per workload/variant produced the following means:

| Workload | Reference | Cache-head candidate | Throughput change |
| --- | ---: | ---: | ---: |
| Frontier, 3,000 frames | 56.744014 s | 56.814015 s | −0.12% |
| Alien Syndrome, 1,800 frames | 32.928708 s | 32.907706 s | +0.06% |
| Workbench 2.0, 1,800 frames | 22.631357 s | 22.705460 s | −0.33% |

The comparison order was reference, candidate, candidate, reference, with a
three-workload batch for each. All guest endpoints matched and every run
released its allocation and restored MMU/cache/register state. The changes
are small and mixed: there is no useful measured improvement. The shortcut
stays opt-in and is not included in the following candidate. No new live-audio
test was justified by these results.

## Candidate: resolve cycle-classification aliases once

The original cycle classifier reads `table68k[opcode].handler` on each lookup
and then tests the corresponding bit. `--flat-cycles` builds an 8 KiB map for
all 65,536 opcodes immediately after `read_table68k()` and `do_merges()` during
CPU setup. The execution loop and group builder then need only the bit lookup.
The map is rebuilt if CPU setup runs again. It adds no per-dispatch readiness
check and makes no change to which instructions may be translated. Inspection
of the compiled dispatcher shows the classification sequence shrinking from
17 A32 instructions to 10, removing repeated canonical-handler loads and address
calculation. This is an instruction count for that sequence, not a measured
CPU-cycle count; the compiler also changes surrounding layout.

Native UBSan tests compare all 65,536 classifications against the original
lookup over three alias layouts, including unset aliases, opcode zero, the last
opcode, variable-cost instructions and reinitialisation. Existing classification
tests also pass. The Python generator has 100% line coverage, CRAP scores 7/2
and 17/17 selected Python mutations caught. Those figures do not measure
coverage or mutation strength inside emitted C++.

Two fresh-process hardware runs per variant/workload give these means:

| Workload | Grouped JIT reference | Precomputed opcode map | Throughput gain |
| --- | ---: | ---: | ---: |
| Frontier, 3,000 guest frames | 56.761687 s | 54.426943 s | +4.29% |
| Alien Syndrome, 1,800 guest frames | 32.923543 s | 31.567595 s | +4.30% |
| A600 Workbench 2.0, 1,800 guest frames | 22.637699 s | 21.716121 s | +4.24% |

Each three-workload batch ran in reference/candidate/candidate/reference order.
The last reference batch from the cache-list experiment also serves as this
experiment's first reference. All dispatch counts, guest cycles, final PC and
frame hashes match; each run completes clean MMU/cache/register restoration and
memory release. These are headless execution-time measurements, not gameplay
FPS. The complete ARM build also passes the 528-case CPU suite at three addresses,
cancellation/fault recovery and all five full-machine timing fixtures.

The corrected JIT still trails the previous fresh interpreter controls
(47.466952/26.229475/19.000368 seconds respectively). The opcode map remains an
opt-in improvement to the experimental JIT; it does not justify switching normal
play away from the existing default. No firmware or release change was made.

### Live window and AHI check

Alien Syndrome ran for 3,000 guest frames in a Workbench window with a 30 FPS
presentation cap and 32 kHz AHI output. One fresh run per variant measured:

| Measurement | Reference | Opcode map |
| --- | ---: | ---: |
| Boot/execution elapsed | 79.008705 s | 76.197281 s |
| Live-window elapsed | 79.235351 s | 76.438715 s |
| Presented frames | 885 | 953 |
| Nonzero PCM frames | 326,009 | 326,009 |
| AHI queued/submitted/completed count | 1,922,048 each | 1,922,048 each |
| Audio queue-gap observations | 807 | 776 |

The fixed-work execution throughput improves **3.69%**. Both runs finish with
identical dispatch counts, guest cycles, PC and final pixels. AHI reports no
backend error, stops cleanly and drains every submitted buffer. Display shutdown,
MMU/cache/register restoration and memory release complete normally.

The differing presented-frame counts reflect the live scheduling path; this
single pair is not a broad game-FPS benchmark. Queue gaps remain substantial,
and the run was not auditioned. It does not establish stable or gap-free audio.
The previous 6,000-frame diagnostic timeout was not retested or claimed fixed.

Final checks confirm Core1 is idle and the installed launcher/player, preferences
and saved Workbench mode are unchanged. Existing Workbench applications remain
open. All 26 physical runs in this pass completed with clean resource restoration.

## Checks

The uninstrumented cache-head build also passes the 528-case CPU suite at
three addresses, cancellation/fault recovery and all five timing fixtures.
The exported standalone list tests pass independently of the workspace layout.

The profiler's native UBSan test covers sampling, absence of clock reads for
unsampled dispatches, timer wrap, 64-bit accumulation and bounded wire output.
The complete profiled ARM build passes 528 CPU cases at three load addresses,
including cache-tail execution, cancellation and fault recovery. All five timing
fixtures match interpreter cycles, PC, registers/CCR, Chip RAM and pixels;
additional checks verify sampled-counter accounting in both engines. Instruction
model timing values are synthetic and are not used as performance evidence.

Both upstream and candidate cache-list routines pass 10,000 native promotions
against an independent list model, including hash collisions, forward/backward
links and handler changes on an entry already at the head. The Python preparation
helper has four covered executable lines and all four selected mutations are
caught. The initial mutation command followed test-file symlinks back to the
unmodified source; retaining the worker paths corrected that harness error.
The C++ helper tools do not provide coverage/mutation analysis for these files.

An added hardware dispatch-count assertion initially used the older
instruction-sized reference. The first opcode-map run matched the current
grouped reference, including dispatch count; the harness was corrected and
resumed after independently checking that completed result. This was a harness
reference error, not a changed expected guest state or a target failure.

## Build

```sh
python3 scripts/build_uae4arm_jit.py --event-blocks --cache-kib 32768 \
  --movw-constants --armv7-emitter --jit-profile --player --hardware
```

For cache-list promotion, replace `--jit-profile` with `--cache-head`; for the
opcode-map candidate, use `--flat-cycles` instead. Each option uses a distinct
output directory. These build options do not install an application
or change the released build.

## Next investigation

Split the special-state interval into STOP waiting, Copper and other service
work before attempting any change to that path. About 40% of sampled dispatches
in the Frontier run take the interpreter path, but that is a dispatch count,
not the fraction of guest instructions or total runtime. Runtime cycle accounting
for variable-cost instructions is another candidate for study; extending groups
must preserve event deadlines and self-modifying-code checks.

The [Z3660-AMIX review](amiga-uae4arm-z3660-review.md) remains relevant to the
architecture. Its fixed service cadence and real-chipset performance cannot be
transplanted into this full-machine emulator. No firmware change is needed for
this profiler or the cache-list experiment.

## Reproduction and evidence

The build uses UAE4ARM upstream commit
`fc1cb90afd6b5c6d9bb933d111c4c99c90f37688`. Profiler source is in commit
`1fdca3e`; the cache-head candidate is in `99066e4`, and the opcode-map
candidate is in `095cfc9`. Full build manifests,
binary hashes, model/native results and physical logs are in the
[evidence archive](../amiga/records/2026-10-28/uae4arm/jit-profile/). User-supplied Kickstart and disk images are required to repeat the game
runs and are not part of these diagnostic records.

The native list regression can be run against a prepared upstream source tree:

```sh
python3 tests/amiga/uae4arm/jit_lists.py \
  --source .context/uae4arm-review/src/jit/compemu_support.cpp
```

The instruction-model checks require the development Python environment with
Unicorn. Use `--cache32 --event-blocks --movw-constants --armv7-emitter` with
`tests/amiga/uae4arm/jit_guest.py`, then add `--jit-profile`, `--cache-head` or `--flat-cycles`
to match the build. The archived model scripts include cancellation, fault and
full-machine timing checks. The hardware scripts are execution records from the
MCP test environment, not an installer.
