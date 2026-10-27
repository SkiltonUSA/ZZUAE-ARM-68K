# UAE4ARM on the ZZ9000 Cortex-A9

Source review: 26 October 2026. Upstream revision
`fc1cb90afd6b5c6d9bb933d111c4c99c90f37688` from
[Chips-fr/uae4arm-rpi](https://github.com/Chips-fr/uae4arm-rpi).

**Verdict: a credible candidate for an XACP prototype.** Native ARM instruction
generation, NEON display helpers and libretro callbacks fit our existing emulator
architecture. The operating-system adaptation is substantial. The initial diagnostic build has now booted Workbench 1.2 on the physical
ZZ9000; see the [prototype report](amiga-uae4arm-prototype.md). A complete
interactive emulator and gameplay-speed results remain pending.

## Agreed target machines

The requested scope is **Amiga 1000, Amiga 500, Amiga 500 Plus and Amiga 600**.
All profiles use an emulated 68000 at the appropriate PAL/NTSC timing.

| Profile | Chipset scope | Integration priority |
|---|---|---|
| A500 | OCS baseline; later-board ECS Agnus variant separately | First execution and performance baseline |
| A500 Plus | Full ECS | Second profile after OCS passes |
| A600 | Full ECS; model-specific Gayle/IDE behavior | Follow ECS baseline; IDE integration tested separately |
| A1000 | Original chipset behavior and model-specific boot handling | Dedicated compatibility work after the shared OCS path |

A500, A500 Plus and A600 have explicit built-in profile functions in `src/cfgfile.cpp`.
A1000 appears in configuration identifiers and the ROM database, including a
bootstrap ROM entry, but this review did not find a corresponding built-in
A1000 profile or establish its writable Kickstart boot behavior. Those references
alone are insufficient to claim full A1000 support. Validate early chipset timing,
boot handling and reset behavior separately; an A500 profile with an older
Kickstart image is not proof of accurate A1000 emulation.

Requested operating-system coverage is Workbench 1.2, 1.3 and the 2.x family.
Workbench is disk-based software; Kickstart is the firmware image and must be
selected separately. Establish 1.2/1.3 baselines on A1000/A500 and model-appropriate
2.x baselines on A500 Plus/A600. Test 2.x on OCS configurations explicitly; do
not assume every historical ROM/Workbench/model combination works. In particular,
A600-specific IDE support needs appropriate Kickstart support. Exact ROM revisions
and system disks will be recorded with each compatibility result. No ROMs or
Workbench disks are included in the planned distribution.

The 68020/JIT experiment described below is now background research, outside
this implementation scope. Prioritize the 68000 interpreter, chipset event
scheduling, NEON rendering and audio batching while preserving compatibility.
A1200/AGA, CD32 and RTG are outside the agreed target scope.

## What was checked

- Cloned the pinned source into `.context/uae4arm-review`.
- Traced the libretro build, CPU selection, renderer, memory allocation, JIT cache
  operations, coroutine switching and audio callback.
- Compiled the unchanged `neon_helper.s` and `arm_helper.s` with GNU Arm Embedded
  GCC 16.2.0 using `-mcpu=cortex-a9 -marm -mfpu=neon -mfloat-abi=softfp`.
  Both succeeded; relocatable object sizes were 5,192 and 1,124 bytes respectively.
  These sizes include object metadata and are not runtime memory requirements.
- Confirmed that the same compiler configuration does not advertise hardware
  integer division; a deliberately supplied UDIV instruction was rejected.
- Probe commands/results are in `.context/uae4arm-a9-audit/compile-probes.json`.

These are assembly compatibility checks, not a complete emulator build or FPS
benchmark. An initial Apple Clang assembly attempt rejected older conditional
instruction spellings accepted by GNU as. A separate local libco compile stopped
because that standalone compiler installation lacks `assert.h`; it did not test
the coroutine implementation. Neither attempt establishes a runtime failure.

## Fit and required adaptations

| Area | Source finding | XACP approach |
|---|---|---|
| Host CPU | Existing 32-bit ARM code generator and graphics assembly | Dedicated Cortex-A9 target; reuse instruction generation after validation |
| Video | `Retro_Screen`, RGB565/XRGB8888 negotiation, video callback | Existing direct ZZ9000 presentation and bounded buffer-flip protocol |
| Audio | Batched signed 16-bit samples through the libretro audio callback | Existing buffered 68K/AHI delivery; retain Paula stereo initially |
| Input | libretro input callbacks and mapper | Existing Amiga keyboard, mouse and joystick messages |
| Timing | PAL/NTSC cadence and frame yielding | One pacing authority; measure emulation, audio and presentation separately |
| Memory | Linux fixed-address mapping and protection | Runtime-probed Exec allocation with bounded guest memory and explicit mappings |
| Rendering | Separate rendering thread and semaphore/pipe coordination | Synchronous or cooperative work on application Core1 |
| Storage | POSIX file access; hardfile and directory devices launch threads | Preloaded read-only ADF for the first test; bounded 68K file service later |
| Interface | Existing desktop/libretro presentation | Reuse our MUI launcher after the execution prototype passes |

The libretro path already supplies an SDL compatibility layer. It does not need
the full desktop SDL/Guichan interface, but that layer still uses pthreads and
POSIX semaphores. A libretro callback interface alone does not remove OS needs.

## Cortex-A9 details that must be addressed

### Build presets and integer division

`Makefile.libretro` enables `ARM_HAS_DIV` in several presets, including
`unix-neon`. Raspberry Pi 2 settings also select Cortex-A7 and `neon-vfpv4`.
Those presets must not be copied unchanged to the Cortex-A9.

Use Cortex-A9/NEON/VFPv3-compatible compiler options and leave `ARM_HAS_DIV`
undefined. `src/jit/compemu_midfunc_arm2.cpp` already supplies a VFP-based
division path when that define is absent. Preserve it and test quotient,
remainder, overflow and divide-by-zero behavior against the interpreter.
The final floating-point ABI must match every linked component and our XACP
entry/exit convention; the assembly probe's softfp option is not a complete
application ABI validation.

### A500 interpretation and 68020 JIT are different targets

`src/newcpu.cpp` selects the JIT only when `cpu_model >= 68020` and a nonzero
code-cache size is configured. The compatible 68000/68010 path uses the
interpreter. Therefore an A500 compatibility test will not automatically receive
the recompiler's speed benefits. Switching to a 68020 changes the emulated
machine and cannot be used as proof of stock A500 compatibility.

The original feasibility review distinguished two CPU paths:

- A500/OCS, 68000, compatible timing, interpreter.
- OCS or ECS with a 68020 and JIT, for software compatible with that setup.

The original agreed implementation scope was the 68000 path. On 27 October,
the scope expanded to an isolated 68020 JIT investigation. Compilation of the
translation units and a support-layer audit passed; runnable JIT integration
remains pending. See amiga-uae4arm-neon.md. Existing upstream source does not
establish working support in a new XACP port.

### Memory mapping and executable code

`src/od-pandora/pandora_mem.cpp` maps a 16 MiB low guest-address area, attempts
another 144 MiB mapping for Zorro/RTG space and has a 400 MiB fallback layout.
These are Linux mapping strategies, not measurements of resident RAM needed for
an A500. Copying those fixed addresses or allocation strategies into XACP would
be inappropriate.

Start with only the memory needed for the selected emulated machine, plus the
required contiguous low-address representation if retained by the port. Account
for stack, renderer tables, buffers and heap separately; measure high-water usage
before selecting the final allocation size. Keep firmware and other applications'
memory outside all mappings.

`src/jit/compemu_support.cpp` allocates executable cache memory with `mmap`.
`src/jit/compemu_midfunc_arm.cpp` synchronizes generated instructions using a
Linux cache-flush system call. Replace both with our bounded code allocation and
verified A9 instruction-cache publication path, including required data-cache
maintenance and barriers. Audit the SIGSEGV-based direct-memory recovery path;
Linux signals cannot simply be treated as firmware exception handlers.

### Rendering and register state

`drawing_init()` in `src/drawing.cpp` creates a render thread. Scanline work is
queued through a pipe; end-of-frame waits for that thread. For XACP, invoke the
same rendering stages synchronously or schedule them cooperatively on Core1.
Simply removing the thread would leave drawing or synchronization incomplete.
Do not use firmware Core0 as a second application renderer.

`libretro/libco/armeabi.c` switches integer registers and stacks, but its switch
assembly does not save d8–d15. A port using compiler-generated VFP/NEON across
coroutine yields must preserve the required floating-point state, or replace
the coroutine mechanism with an explicit step interface. This is an integration
risk identified by inspection, not a reproduced upstream failure.

## What transfers from our existing work

- Runtime-probed ZZ9000 memory, private cacheable execution and uncached control
  messages, with register/MMU/cache restoration on exit.
- Direct display buffers, completion tracking and frame pacing.
- Batched audio delivery and 68K input/file coordination.
- Native correctness checks followed by physical bounded runs and clean-exit
  verification.
- Profiling before changing hot paths; SIMD for suitable planar-to-pixel and
  copy operations. Existing NEON helpers already cover several of these tasks.

DOSBox translates x86 instructions; UAE4ARM translates 68K instructions. The
execution infrastructure is reusable, but neither DOSBox's instruction emitter
nor its measured speed gains can be transferred as UAE4ARM results.

## Recommended prototype sequence

1. Create an isolated ARM build with a small platform adapter. Initially omit
   networking, host-directory devices, CD audio, RTG and archive/image plugins
   that require extra libraries. Preserve upstream licensing and attribution.
2. Run the interpreter against a deterministic original test ROM/program and
   read-only ADF. Verify CPU results and rendered-frame checksums; exercise stop
   and cleanup. Use an appropriately licensed or user-supplied Kickstart when
   testing software that needs it.
3. Measure a bounded A500/OCS run on the physical A9 with drawing enabled. Record
   time spent emulating, rendering and waiting. A static screen is not enough
   evidence for game-speed claims.
4. Extend the baseline to A500 Plus/ECS, A600 and A1000-specific behavior. Test
   CPU exceptions, disk loading, Copper/Blitter timing, sprites, reset and audio
   across all four profiles. Keep JIT disabled for these 68000 configurations.
5. Add direct display and buffered audio. Measure sustained PAL and NTSC timing,
   underruns, input response, frame completion and teardown across repeated runs.
6. Add MUI/media selection for A1000, A500, A500 Plus and A600 only after the core's
   performance and lifecycle are demonstrated. Include per-profile PAL/NTSC,
   compatible memory configurations, Kickstart selection and Workbench disk/hardfile
   selection. Add hardfile/IDE support after the floppy-based boot tests.

Proceed with the isolated prototype. The evidence supports technical feasibility,
but does not yet support a promise of 50/60 FPS, AGA game speed or CD32 compatibility.

## Source references

All links below use the reviewed revision:

- [Build options](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/Makefile.libretro)
- [Libretro callbacks](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/libretro/core/libretro-core.cpp)
- [CPU execution selection](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/src/newcpu.cpp)
- [ARM division paths](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/src/jit/compemu_midfunc_arm2.cpp)
- [Memory adaptation](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/src/od-pandora/pandora_mem.cpp)
- [Rendering thread](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/src/drawing.cpp)
- [ARM coroutine switching](https://github.com/Chips-fr/uae4arm-rpi/blob/fc1cb90afd6b5c6d9bb933d111c4c99c90f37688/libretro/libco/armeabi.c)
- [XACP execution framework](https://github.com/Xanxi-Amiga/XACP-ZZ9000)
