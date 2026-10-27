# ZZUAE guest JIT: first bounded hardware execution

The isolated CPU diagnostic now executes upstream UAE4ARM guest translations on
ZZ9000 Core1. **216 comparisons against the interpreter passed on the physical
A4000TX in each of two fresh runs**, with zero mismatches and clean MMU/cache/register restoration.
This is a development milestone, not a JIT-enabled Workbench or game player.
The installed 0.5.4-dev interpreter and downloadable 0.5.3 Beta are unchanged.

## What runs

The diagnostic builds the pinned UAE4ARM core (`fc1cb90afd6b5c6d9bb933d111c4c99c90f37688`)
with matching 68020 interpreter/JIT tables and register layout. Nine fixtures
run 24 times each, warming the translator and comparing all 16 guest data/address
registers, architectural flags, PC and 512 bytes of RAM/stack state. They cover
arithmetic, ADDX/Scc flags, reads/writes, unsigned/signed division fallback,
conditional branches, MOVEM, shifts and modification of an already-translated
immediate. The physical result hash is `02ed083b`; the compiler emitted 43
translated instruction sites and two fallback sites. These are code-generation
counts, not dynamic instruction counts or a performance ratio.

The instruction model additionally observed 1,792 generated-block entries per
run at three allocation addresses, including the address used on hardware.
Cancellation and an injected data-abort landing test passed in the model, with
executable-page or exception-vector restoration as applicable. These tests do
not simulate physical cache coherence or establish hardware fault recovery.

## Port changes

- Use the existing owned executable arena and A9 cache-publication hooks instead
  of Linux mmap/cache services; bound the JIT cache to 512 KiB.
- Route generated memory reads/writes and indirect PC translation through UAE
  memory banks. The guest banks are separate allocations, not Linux natmem.
- Bound traces to 32 instructions, disable following constant jumps and return
  after each dispatch in this CPU-only fixture.
- Retain integer division in the interpreter: upstream's A9 division translator
  emits VFP, whose full exception/non-local-exit context is not integrated yet.
- Initialise the bare-metal allocator from zeroed BSS and release its pools
  explicitly; remove dependencies on C++ static destruction.
- Add diagnostic-only private exception vectors and progress reporting. Restore
  the original VBAR before returning. The normal player does not use this guard.

## Why the initial physical tests hung

Three early physical runs timed out during initialisation, before the first
guest block. The third included exception capture but reported no exception.
All had passed the instruction model. Their logs are retained as failures;
none passed cooperative register/cache restoration. The existing launcher
reset Core1 to idle before freeing its allocation.

Inspection found `regs` at BSS offset `0x640010`. Because an Exec allocation can
start partway through a page, that location shared the last non-cacheable,
shareable control page. Once JIT cache initialisation completed, a mapping flush
called `set_special(0)`, which contains an LDREX/STREX retry loop on those flags.
This explained a potential spin without an exception.

The successful build adds a 4 KiB gap before private BSS objects, placing `regs`
at `0x641010`, wholly in private cached memory. It preserves the atomic operations
and shared-memory policy. This layout change alone changed the instrumented
hardware run from timeout to success. The retry-loop diagnosis is supported by
source/disassembly and this comparison; the stalled hardware PC was not captured.
A model layout assertion now rejects the previous boundary placement.

The fixture took about 11.3 ms after initialisation in the first successful run.
That is a mixed warmup/compile/execute correctness workload, **not** an interpreter
speed comparison, game FPS measurement or evidence of A500 timing accuracy.

## Reproduce and evidence

With the existing pinned toolchain and core checkout prepared:

```sh
python3 scripts/build_uae4arm_jit.py --hardware
python3 tests/amiga/uae4arm/jit_guest.py --mmu
python3 tests/amiga/uae4arm/jit_guest.py --mmu --cancel
python3 tests/amiga/uae4arm/jit_guest.py --mmu --fault
```

Model tests require Unicorn. Outputs are isolated under
`.context/amiga/uae4arm/jit-execution`; the script does not install or start the
hardware executable. Physical runs used the established mapping probe,
application-owned Core1 lifecycle and reset-before-free launcher.

[Raw physical/model logs and artifact receipt](../amiga/records/2026-10-27/uae4arm/guest-jit/)
include the unsuccessful attempts. No commercial ROM is needed by this fixture.

## Remaining before player integration

The diagnostic uses 68020 tables and has no chipset scheduler. A1000/A500 CPU
semantics, exception delivery, bounded event/interrupt dispatch, wider
self-modifying-code tests and game/Workbench differential checks remain.
Guest FPU/VFP context is unresolved; division fallback deliberately avoids it.
No launcher JIT option or performance gain is claimed yet.

## Reference documents

The supplied **ARM Architecture Reference Manual ARMv7-A/R, DDI 0406C.d** is
relevant to this work. Section A3.5, page A3-128, specifies publication of modified
instructions: clean data to the point of unification, DSB, invalidate instruction
cache and branch predictor, DSB, then ISB before execution. The existing owned
cache hook follows this order using local A9 maintenance operations.

The supplied **ITU-T H.264 (02/2014)** PDF specifies the video codec; it is not an
ARM processor manual. It belongs with future video-decoder research.
The [PathPartner Cortex-A9 H.264 optimisation article](https://www.design-reuse.com/article/60871-efficient-simd-and-algorithmic-optimization-techniques-for-h264-decoder-on-cortex-a9/)
provides relevant profiling/data-layout principles, but its decoding gains do
not predict emulator gains. Neither PDF is redistributed in this source backup.
