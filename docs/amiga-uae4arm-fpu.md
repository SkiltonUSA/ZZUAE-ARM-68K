# ZZUAE experimental guest FPU

The optional ZZUAE-FPU player exposes a 68882 to the emulated 68020. The
launcher offers FPU Off / 68882 (experimental) with either accelerated CPU
mode. The compatible 68000 player remains separate, and FPU is Off by default.
This is an emulated Amiga FPU backed by ARM VFP, not direct guest access to ARM
registers and not FPGA logic.

## Execution and precision

Reuse the pinned UAE4ARM fpp.cpp / fpp_native.cpp backend. Arithmetic runs on
Core1; native double addition/multiplication/division and square root use the
Cortex-A9 VFP hardware. The x87 work in ZZDosBox is separate. JIT translation of
FPU instructions remains disabled: the integer JIT falls back to the FPU
interpreter, whose arithmetic implementation uses VFP. Transcendentals use the
pinned picolibc libm.

The upstream ARM backend calculates in 64-bit double, **not full 68882 extended
precision/range**. Extended-format memory transfers are supported, but this does
not make internal calculations 80-bit accurate. Full exception/NaN and demanding
numerical-software compatibility are not established. It is labelled experimental.

ARM-host rounding uses the guest FPCR. The port provides VFP integer conversion
and square root, plus a rounding helper for FINT, rather than relying on the
rounding behaviour of a library built under another floating-point ABI.

The complete worker call saves/restores D0–D31 and FPSCR, including cancellation,
fatal exits and compiler cleanup. CPACR/FPEXC are not changed. A disabled or
unavailable VFP/NEON context causes a clean diagnostic error before execution.
Runtime state comparisons report state_mismatch; a nonzero result fails the run.
The scalar 68000 player continues using its existing integer-only contract.

## Software must use an FPU

Enabling this option does not turn integer operations into floating-point
operations. A game or application must issue 68881/68882 instructions, or use an
FPU-aware library/build, to gain anything. In particular, the standard A500
Frontier intro benchmark is not evidence that Frontier uses an FPU. The player
logs total FPU dispatches, data operations and context saves/restores. Total
dispatches alone are not evidence of game arithmetic: AmigaOS can save and
restore FPU state while scheduling tasks.

## Build and validation

First build the pinned experimental JIT core, then:

```
python3 scripts/build_uae4arm_fpu.py --hardware
```

The builder uses the existing matching JIT ABI objects in a separate
.context/amiga/uae4arm/fpu-execution directory. Only the new FPU backend is
compiled with softfp/VFPv3; surrounding code remains integer-only. The instruction
audit permits VFP only in the backend, state routines and explicit libm callees.

The guest fixture is assembled from tests/amiga/uae4arm/fpu_guest.S. It repeats
arithmetic, square root, extended-format stores, directed/ties-even rounding,
FSAVE/FRESTORE and a loop branch. Both 68020 interpreter and warmed JIT fallback
pass in the A9 instruction model. Lifecycle tests cover success, cancellation,
invalid settings, rejected vectors, cleanup abort, unlimited stop and unavailable
VFP, verifying full register restoration. These do not replace physical tests.

The physical A4000TX/ZZ9000 diagnostic passed 576 guest FPU instructions and all
ten expected result words. It checked arithmetic, VFP square root, directed and
ties-even rounding, extended-format storage and FSAVE/FRESTORE.
`state_mismatch=0`; cache/MMU/register restoration and owned-memory release
passed. This is a bounded instruction fixture, not a full FPU conformance suite.

The FPU-Off instruction-model run rejects the fixture without producing any of
its result words. Model tests also exercised the same diagnostic entry point as
the physical run. The supplied Frontier: Elite II disk reached its animated intro and completed
6,000 guest frames in both accelerated modes with AHI and native PAL fullscreen.
Both restored the host and released the allocation. Audio-device errors were
zero; late queue observations remain, so this is not an audible-stability claim.

The final 68020-interpreter run recorded:

| Activity | Count |
|---|---:|
| Total FPU dispatches | 15,732 |
| FPU data operations | **0** |
| FSAVE | 7,831 |
| FRESTORE | 7,836 |
| ARM floating-point state mismatches | **0** |

The remaining 65 dispatches are other FPU/control handling. The data-operation
counter runs in the upstream arithmetic dispatcher after operand/availability
checks and includes FMOVE as well as calculations. Its zero value means this
observed intro did not perform FPU data calculations. Save/restore activity must
not be reported as Frontier floating-point acceleration. Later gameplay or a
different executable would need its own measurement.

No speedup is claimed. The experimental 68020 modes also have different CPU
timing from the normal 68000 profile; retain the compatible mode for games
that do not need the FPU.


Reproduce the synthetic validation after building (Python requires Unicorn):

```sh
python tests/amiga/uae4arm/check_machine.py 2 --elf .context/amiga/uae4arm/fpu-execution/uae-machine.elf --synthetic-rom --profile 1 --ram1m --engine 1 --neon --fpu-fixture
python tests/amiga/uae4arm/check_machine.py 2 --elf .context/amiga/uae4arm/fpu-execution/uae-machine.elf --synthetic-rom --profile 1 --ram1m --engine 2 --neon --fpu-fixture
python tests/amiga/uae4arm/machine_lifecycle.py .context/amiga/uae4arm/fpu-execution/uae-machine.elf fpu-verify success cancel invalid-options cleanup-abort vector-rejected unlimited-cancel fpu-unavailable
```

Add `--fpu-off` to the interpreter fixture to check that disabling the guest FPU
prevents its result writes. The diagnostic distinguishes 288 data operations and
24 each of FSAVE/FRESTORE in its 576 total FPU dispatches.


## Development log

1. Confirmed the original player rejected an original guest FPU fixture.
2. Integrated the pinned UAE native FPU backend with an isolated player and
   complete ARM floating-point state boundary. Corrected host rounding helpers.
3. Passed interpreter/JIT fallback arithmetic and failure/cancellation tests;
   ran the fixture on the physical ZZ9000.
4. Ran the supplied Frontier intro with both accelerated CPU modes.
5. Split total FPU dispatches into data and context activity. The new fixture
   assertion first failed with missing counters, then passed with exact counts.
6. Repeated the physical intro with the detailed counters: no FPU data operations.
7. Built optional-player ZIP/AmiPkg packages, checked hashes/signature, and
   installed the new launcher/player while preserving saved settings.
8. Verified the installed MUI FPU selection, windowed Workbench launch and F10
   exit: 785 display presentations, no FPU-state/host-restoration errors, and
   unchanged emulator/display preferences. Returned the UI to compatible CPU.

Selected logs and executable identities are in
`amiga/records/2026-10-27/uae4arm/fpu/` in the standalone source repository.
The development package includes the three players; the public 0.5.3 download
has not been replaced by this work.
