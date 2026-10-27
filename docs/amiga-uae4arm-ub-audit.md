# ZZUAE UB-mode review

Reviewed the guest-JIT integration, launcher settings and build adapters introduced
in `3c43306`, using the requested [UB-mode protocol](https://github.com/unclebob/ub-mode).
The review found and corrected a fatal-error lifetime problem. It does not change
the earlier performance findings or resolve the experimental audio/timing issues.

## Findings and corrections

| Finding | Correction | Evidence |
|---|---|---|
| The fatal guard ended before `compiler_exit()`. An abort during cleanup entered the runtime's WFE loop instead of returning an error. | Keep the `setjmp` boundary in the outer player entry, covering execution and compiler cleanup. | Inject the real runtime `exit(99)` at cleanup. The preserved old ELF reaches WFE with its guard disabled; the corrected ELF returns error 99 and restores VBAR. |
| Normal-player early returns could leave `uae_fatal_active` pointing at an expired stack frame. | Clear the guard at the common exit, including invalid-option and cancellation paths. | Real ARM entry tests check rejected options, normal completion and cancellation. |
| Rejected vector setup in the CPU-only diagnostic left its fatal guard active. | Clear it before returning setup error 98. | Force high-vector mode in the model; verify error 98, inactive guard and unchanged VBAR. |

The fatal boundary remains an integer-only context. A fatal worker exit is
terminal: the host must restore/reset Core1 through its existing teardown path.
The fix does not attempt to resume a corrupted heap or re-enter failed cleanup.

## Verification

- Rebuilt compatible and JIT ARM workers.
- JIT lifecycle tests: success, cancellation, invalid options, rejected vector
  setup and injected cleanup abort all pass.
- Compatible lifecycle tests: success, cancellation and invalid options pass.
- Successful/cancelled JIT runs restore their executable-page permissions.
- All 240 interpreter/JIT comparisons pass at three allocation addresses.
- Launcher configuration tests pass with AddressSanitizer and UndefinedBehaviorSanitizer.
- The lifecycle fixture uses an original synthetic ROM and blank disk data;
  it requires no Kickstart or commercial game files.

These are native and instruction-model checks. Deliberate hardware fault recovery
was not tested, and the installed Amiga binaries were not replaced during this
review. No performance improvement or new release is claimed.

## UB companion tools

The supplied tools support Python, not C/C++ or ARM assembly. Their numbers must
not be presented as runtime-emulator coverage or a whole-project quality score.

| Tool | Scope | Result |
|---|---|---|
| Crapper | Build-adapter functions | `prepare`: CC4, coverage/CRAP unavailable. |
| Crapper + coverage | `audit_integer_context` only | CC8, 100% measured function coverage, CRAP8.0. Top-level build execution is outside this measurement. |
| Dryer | Three build adapters, threshold0.8 | No duplicate candidates. |
| Mutator | `audit_integer_context` only | Six executed mutations, all six killed. |
| Mutator scan | JIT preparation adapter | 27 candidate sites; not executed, so no mutation-score claim. |

The instruction-audit tests exercise the actual production function through its
AST, avoiding the build script's top-level compilation side effects. They check
scalar acceptance, rejected floating-point instructions, the exact permitted
SIMD leaf names, function-boundary handling and rejected hardware division.
One mutation initially survived because the test double ignored the subprocess
text/bytes contract; correcting that test double killed the survivor.

No blanket null-check additions, unrelated refactoring or source duplication
removal was justified by this review. The short architectural FPU entry points
remain separate because the core requires their distinct signatures.

[Selected evidence and action log](../amiga/records/2026-10-27/uae4arm/ub-audit/).

## Reproduce the lifecycle checks

With the documented toolchain and Unicorn environment prepared:

```sh
python3 scripts/build_uae4arm_machine.py
python3 scripts/build_uae4arm_jit.py --player
python3 tests/amiga/uae4arm/machine_lifecycle.py .context/amiga/uae4arm/uae-machine.elf success cancel invalid-options
python3 tests/amiga/uae4arm/machine_lifecycle.py .context/amiga/uae4arm/jit-execution/uae-machine.elf success cancel invalid-options vector-rejected cleanup-abort
python3 tests/amiga/uae4arm/machine_lifecycle.py .context/amiga/uae4arm/jit-execution/guest.elf vector-rejected
python3 tests/amiga/uae4arm/instruction_audit.py
```
