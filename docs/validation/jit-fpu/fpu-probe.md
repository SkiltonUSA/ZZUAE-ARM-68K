# Physical FPU diagnostic

At the time of this diagnostic, the full FPU player retained its stock-clock gate.
The subsequent [full-player work](../fpu-clock/README.md) is recorded separately. A separate diagnostic host
runs the recorded payload's bounded `MB_VERIFY` arithmetic fixture without
booting a guest, rendering frames or pacing audio. It accepts the measured timer
ranges for 666.7 and 800 MHz, but does not change the PLL or enable gameplay at
another clock rate. Defining `UAE_BOOT` when compiling this host is an error.

```sh
python3 scripts/build_fpu_probe.py /path/to/recorded/fpu-execution/machine \
  --output /path/to/isolated/probe
```

The build uses the pinned Amiga cross-compiler image and preserves the ARM
payload exactly. It copies **both `mmu.h` and its paired `mmu_plan.h`**, recording
their hashes. The first diagnostic build omitted the latter and read generic
report offsets instead: arithmetic and VFP checks passed, but the host correctly
refused to report a clean overall result. This was a diagnostic build-input error,
not evidence of guest arithmetic or actual MMU restoration failure.

The guest fixture checks arithmetic, square root, directed rounding,
ties-to-even, extended-format storage and 24 FSAVE/FRESTORE rounds. The ARM
wrapper compares all 32 D registers and FPSCR against its entry snapshot. The
host treats a state mismatch as failure and retains register/cache-witness
checks during teardown.

This is the upstream ARM double-backed FPU path: it does not establish complete
68882 extended-precision accuracy, all exception behaviour or game compatibility.
It also does not validate the full FPU player's clock scaling, audio or JIT/FPU
interaction. The interpreter remains the normal default.


Two fresh-process runs passed on the physical A4000TX at the retained 800 MHz
clock. Each completed 576 FPU instructions, 288 data operations and 24 save/restore
rounds, with zero host VFP-state mismatches. Register/cache-witness restoration
passed and allocated memory was released. Final status: Core1 idle, Core0 AGA
inactive, clock fault zero, 59.8 C; bridge reservation released.

[Successful run logs](fpu-hardware.txt) · [Build identities](fpu-build.json) ·
[First host-layout failure](fpu-host-layout-failure.txt).
No firmware, clock, installed player or user setting changed. This diagnostic is
not a replacement for the normal FPU player and is not added to the installer.
