# Experimental JIT and FPU compatibility

Thirteen instruction-model configurations pass using the recorded **0.6.0-dev
ARM payloads**, with a 32 MiB executable cache inside a 64 MiB test allocation.
These payload identities are separate from the published 0.6.1 Beta launcher.
No emulator or installed binary changed in this pass.

- JIT self-modifying-code checks pass without the fixture explicitly flushing
  translated code, at three relocation addresses.
- Cancellation and injected-fault recovery pass at the same three addresses,
  including executable-page cleanup and exception-vector restoration.
- JIT and interpreter each pass guest FPU arithmetic, square root, extended
  storage, directed rounding, ties-to-even and full host VFP-context restoration
  under four inherited FPSCR inputs.
- Both engines pass the handled missing-FPU exception test, including the
  saved instruction PC and recovery after FRESTORE.

The harness now accepts an explicit FPU fixture path and compares FPSCR against
its accepted read-back value. Unsupported bits read as zero; comparing against
an unfiltered requested value caused a false failure. No guest assertion was
removed and no emulator correction was needed for these cases.

```sh
python3 scripts/test_jit_fpu_compatibility.py \
  --jit /path/to/recorded/guest.elf \
  --fpu /path/to/recorded/uae-machine.elf \
  --program /path/to/recorded/fpu_guest.bin
```

Requires Unicorn and the existing LLVM-based test tooling. The runner writes
logs separately and never rebuilds or replaces the supplied players.
[Input hashes and configuration list](results.json) identify the exact artifacts;
[results](results.txt) contain the per-case output.

Physical JIT/FPU validation remains pending. A later A600 interpreter baseline
attempt lost bridge/network contact before completion; its JIT comparison was
not started. See the [unresolved hardware attempt](hardware-attempt.md). Instruction-model tests do not
establish real cache coherency, audible quality, gameplay compatibility or speed.
The optional FPU/Cyclone players retain their stock-clock gates; this pass does
not validate them at 800 MHz. The interpreter remains the default.
