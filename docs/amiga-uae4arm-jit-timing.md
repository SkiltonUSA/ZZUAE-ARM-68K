# ZZUAE JIT timing investigation

> **Timing status:** physical performance figures in this report predate the
> [RAM-disk stall investigation](amiga-uae4arm-ram-disk-stall.md). RAM-disk
> occupancy was not consistently controlled; timings and percentage gains need
> matched remeasurement. Correctness and instruction-model results are separate.

The 32 MiB cache experiment changed Frontier's final state relative to the
512 KiB cache. Matching repeated runs of each build does not establish that
both builds emulate the same sequence of chipset events. This investigation
reproduced the causes and produced an isolated timing mode that matches the
interpreter on the tested Frontier run with both cache sizes. The installed
player and release remain unchanged because the diagnostic is slower.

## Reproduced differences

A small synthetic ROM reads VHPOSR, executes arithmetic, reads VHPOSR again,
and stores both readings in Chip RAM. After one guest frame, the ordinary JIT
and the matching 68020 interpreter have different cycle counts, PCs,
registers and Chip RAM. The regression executes the real ARM payload in an
instruction model; it does not verify physical cache maintenance or timing.

Three relevant timing mechanisms were reproduced:

- While learning a block, `execute_normal()` advances chipset time after each
  interpreted instruction. Warm generated code debits the accumulated block
  cycles at its exit. Hardware-register reads therefore observe different
  event positions as a block becomes compiled.
- Generated exits use the cycle total observed when the block was learned.
  Instructions such as DBRA and conditional branches can return different
  cycle counts on later executions. Instruction-sized blocks alone do not
  address this difference.
- Compilation debits the guest countdown to account for compilation cost. That
  debit can reach chipset events during interrupt handling. Cache invalidation
  also changes the countdown to escape generated code. The diagnostic preserves
  the guest countdown across compilation and resets host-only validation
  bookkeeping before dispatch.

The isolated `--instruction-timing` build limits traces and the unoptimised
execution path to one instruction. Variable-cycle instructions use the matching
interpreter directly, retaining each runtime cycle count. Compiler bookkeeping
does not contribute guest cycles. A generated map of constant-cycle handlers
comes from the pinned 68020 interpreter sources. Tests cover beam reads, both
DBRA outcomes, forced level-3 interrupts and metadata reclamation. These checks
do not claim cycle-exact 68000 bus emulation; the reference is this port's
68020 interpreter.

The state comparison masks unused CPSR bits in the internal NZCV storage; it
compares all four architectural NZCV flags and the separate X flag. The original
beam failure also changed cycles, PC and RAM, independently of flag storage.

## Metadata budget

The first 32 MiB diagnostic run exhausted its block-metadata pool after
11,159,498 dispatches. A second run reported the ARM call site, which resolves
to the failed block-pool allocation. Both failures unwound cleanly; they were
not successful 3,000-frame runs.

Instruction-sized traces create more metadata than ordinary blocks. The
isolated mode now reclaims the cache between dispatches when active metadata
exceeds 2 MiB, within the existing 8 MiB general heap. Reserved block entries
are returned to their pool during hard flush rather than losing their
references. A 20,000-instruction synthetic ROM exercised two metadata-budget
flushes and matched the interpreter's state. This budget can force reclamation
before the 32 MiB code arena fills; it is not a claim of full-cache residency.

## Commands

```sh
python3 scripts/build_uae4arm_jit.py --instruction-timing --cache-kib 32768 --player --hardware
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/jit_timing.py \
  --elf .context/amiga/uae4arm/jit-execution-32768-instruction-timing/uae-machine.elf \
  --cache32 --fixtures beam branch irq pressure --output .context/amiga/uae4arm/jit-timing/model
```

The normal build, installed launcher and release remain unchanged.
The timing mode is a correctness reference, not a performance improvement.

## Regression results

| Build | Beam reads | Changing branch cycles |
| --- | --- | --- |
| Ordinary block JIT | Fails: cycles/PC/RAM differ | Not needed for the first failure |
| One-instruction traces alone | Pass | Fails |
| One-instruction traces + runtime variable-cycle dispatch, 512 KiB | Pass | Pass |
| One-instruction traces + runtime variable-cycle dispatch, 32 MiB | Pass | Pass |

The existing 432-case translated CPU suite passed at three load addresses with
MMU protection, including generated code near the end of the 32 MiB cache.
Cancellation and injected ARM data-abort checks restored the executable pages
and vector base. Nine cycle-map tests passed; all 14 selected Python mutations
were detected. The final matrix also passes forced interrupts at both cache sizes and metadata
pressure at 32 MiB. These checks complement the physical runs below.

## Physical Frontier comparison

Fresh-process runs on the A4000TX/ZZ9000, XX19c/XACP1.7: same Frontier disk1,
Kickstart1.3, A500 chipset profile, expanded RAM, 68020 engine, 3,000 guest
frames, MAX, no live display/audio/input, volatile disk writes. Media was not
modified. Each row below is one physical run, not a repeated performance study.

| Mode | Seconds | Guest cycles | Final PC | Frame hash |
| --- | ---: | ---: | --- | --- |
| 68020 interpreter | 48.246432 | 426273780 | `00c3b724` | `1566eac0` |
| Ordinary JIT, 512 KiB | 47.015101 | 426273786 | `00c30fb0` | `00b713c0` |
| Ordinary JIT, 32 MiB | 45.711487 | 426273835 | `00c3d72c` | `6cf84f80` |
| Timing diagnostic, 512 KiB | 63.999761 | 426273780 | `00c3b724` | `1566eac0` |
| Timing diagnostic, 32 MiB | 58.952610 | 426273780 | `00c3b724` | `1566eac0` |

Both corrected cache sizes match the interpreter's cycle count, final PC and
frame hash after all 3,000 frames. All five listed runs restored the hardware
registers/MMU/cache witnesses and released their allocation. Hardware logs do
not contain a full guest-RAM/register digest; those deeper comparisons belong
to the synthetic ARM instruction-model tests above.

The corrected 32 MiB run took 58.95 s versus 64.00 s for 512 KiB, but both were slower
than the 48.25 s interpreter reference. These are startup/intro run times, not
Frontier's unique 3D-frame FPS. Dispatch counts differ because JIT cache lookup
and compilation can return without executing a guest instruction.

The next performance work should retain this timing reference while testing
larger event-aware blocks and runtime branch costs. Literal loads versus
MOVW/MOVT is a separate experiment. The diagnostic has not been promoted to a
launcher option or release.

[Raw hardware/model records and build hashes](../amiga/records/2026-10-27/uae4arm/jit-timing/).

## Architecture references

The supplied [ARMv7-M manual](https://web.eecs.umich.edu/~prabal/teaching/eecs373-f10/readings/ARMv7-M_ARM.pdf)
is DDI0403C. It covers the M profile and Thumb execution. ZZ9000 uses
[Cortex-A9 / ARMv7-A](https://support.arm.com/compute-ip/cortex-a9), so A-profile
cache/MMU, exception and NEON documentation remains the reference for this port.

The accompanying immediate-constant discussion is relevant to the A32 emitter:
encodable values can use MOV/MVN; MOVW plus MOVT can construct an arbitrary
32-bit value without a literal-pool read. Instruction counts, relocation and
code-cache pressure must be measured together. The existing
`tests/amiga/uae4arm/jit_immediate.py` regression covers the corrected unsigned
A32 immediate encoding. No new constant-loading performance gain is claimed here.

Literal-load reach is local to each instruction, independent of total cache
capacity. The pinned emitter's `LOAD_U32` uses `data_long_offs()` and PC-relative
LDR in its current path; its `ARMV6T2` path uses MOVW/MOVT. Its existing pool
tracker reserves 768-byte data buffers, branches around them, and uses a
4,064-byte maximum distance. The confirmed hardware failure was metadata
allocation, not a literal-range error. Compiler flags for C/C++ support code
do not rewrite the runtime emitter. A future comparison
must audit generated addressing, relocation and code growth, and test the other
emitter paths affected by that feature switch. No feature switch was enabled as
part of this timing investigation.

## Constant-loading follow-up

The isolated MOVW/MOVT test now completes the same Frontier workload with a
1.17% throughput gain over this 32 MiB timing reference, with matching guest
cycles, final PC and frame hash in all four paired runs. It changes only
`LOAD_U32`; global ARMV6T2 remains disabled. The installed build is unchanged.
[Implementation, repeated measurements and limits](amiga-uae4arm-jit-constants.md).
