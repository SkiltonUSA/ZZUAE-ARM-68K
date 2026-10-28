# ZZUAE JIT constant-loading experiment

This experiment replaces the runtime JIT's `LOAD_U32` literal load with its
existing upstream MOVW/MOVT implementation. It is an isolated build option,
`--movw-constants`, measured against the corrected instruction-timing reference
with a 32 MiB translation cache. The normal player and release are unchanged.

## Scope

MOVW constructs the lower 16 bits and clears the upper half; MOVT supplies the
upper half when needed. The generated sequence needs no literal-pool data read.
This does not guarantee faster emulation: two instructions may replace one
load, and code-cache occupancy and compilation cost can also change.

Only `LOAD_U32` is selected. The global `ARMV6T2` switch remains disabled;
other instruction-generation paths and 16-bit literal helpers are untouched.
The preparation script reuses the pinned upstream macro definitions rather
than introducing another A32 encoder. Comparing generated sources confirms
that only `codegen_arm.cpp` and its required macros in `codegen_arm.h` differ.

## Correctness checks

The emitter harness executes 7,830 constant/register combinations at each of
two addresses using the Cortex-A9 instruction model. It checks the value,
other registers, flags and absence of data reads. UBSan checks the native
emitter harness. The preparation test also checks that adjacent emitter code
is preserved. All 12 selected Python mutations are detected; the preparation
helper has 100% line coverage and CRAP 2. These metrics cover the Python
preparation helper, not the C++ JIT as a whole.

The complete candidate also passes 432 translated CPU cases at three load
addresses with MMU protection, including execution near the 32 MiB cache end.
The instruction-model timing matrix matches the interpreter's cycles, PC,
registers/CCR, Chip RAM and pixels for beam reads, changing branch costs,
interrupts and metadata pressure. Cancellation and injected data-abort recovery
restore executable-page permissions and the vector base.

## Reproduce

```sh
python3 scripts/build_uae4arm_jit.py --instruction-timing --cache-kib 32768 --movw-constants --player --hardware
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/jit_constants.py \
  --source-dir .context/amiga/uae4arm/jit-execution-32768-instruction-timing-movw/src/jit
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/jit_guest.py \
  --cache32 --instruction-timing --movw-constants --mmu
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/jit_timing.py \
  --elf .context/amiga/uae4arm/jit-execution-32768-instruction-timing-movw/uae-machine.elf \
  --cache32 --fixtures beam branch irq pressure --output .context/amiga/uae4arm/movw/model
```

The upstream emitter is pinned to UAE4ARM commit
`fc1cb90afd6b5c6d9bb933d111c4c99c90f37688`.

## Physical Frontier results

A4000TX/ZZ9000, XX19c/XACP 1.7, fresh processes in A1/B1/B2/A2 order.
Both builds use the corrected instruction-timing mode, 32 MiB JIT cache,
Frontier disk 1, Kickstart 1.3, A500 profile, expanded RAM, 68020 JIT,
3,000 guest frames and MAX. No live display, audio or input; disk writes are
volatile. Background Workbench applications were retained for all four runs.

| Constant loading | First run | Second run | Mean |
| --- | ---: | ---: | ---: |
| Literal-pool LDR | 58.945569 s | 58.950660 s | 58.948115 s |
| MOVW/MOVT | 58.269194 s | 58.266316 s | 58.267755 s |

MOVW/MOVT improved throughput by **1.17%** on this workload
(1.15% less elapsed time). All four runs completed
3,000 frames with guest cycles `426273780`, final PC `00c3b724` and frame hash
`1566eac0`. Each restored the MMU/register/cache witnesses and released its
allocation without reported errors.

This is a small, repeatable improvement in two runs per variant, not a broad
emulator benchmark. These are startup/intro execution times, not Frontier's
unique 3D-frame FPS. The hardware comparison does not include a complete
RAM/register digest; deeper state comparisons are the model tests above.
Audio and live presentation performance were not measured in this experiment.

The constant helper avoids literal data reads, but this measurement does not
separate their cost from instruction count, compilation or cache effects.
Peak generated-code residency was not measured. The candidate remains slower
than the earlier 48.25 s interpreter reference and is retained as an opt-in
experiment rather than promoted to the installed player or release.

The next substantial target is larger event-aware JIT blocks with correct
runtime branch costs, retaining the timing regression matrix as a gate.

[Raw tests, hardware logs and build hashes](../amiga/records/2026-10-27/uae4arm/jit-constants/).
[Instruction-timing investigation](amiga-uae4arm-jit-timing.md).
