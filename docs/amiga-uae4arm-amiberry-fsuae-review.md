# Amiberry ARM32 and FS-UAE review

Source inspection only; neither application was ported or benchmarked on ZZ9000.

## Amiberry Android fork

Reviewed [mirq/amiberry-android](https://github.com/mirq/amiberry-android) at
`1003e68de3ce6f17afdb4f7cdf2477503258e8fd`.

Its useful component for ZZUAE is the 68K-to-ARM32 compiler under
`src/jit/arm`, including instruction generation, register allocation and flags
handling. This is a much closer architectural match than an emulator whose
guest CPU is ARM. Its SDL-based platform is not an XACP application.

A concrete portability hazard is `cmake/SourceFiles.cmake`: its ARM32 definitions
include `ARM_HAS_DIV`, as well as ARMv6T2 and NEON. The corresponding JIT emits
SDIV/UDIV instructions. Cortex-A9 does not implement these integer divide
instructions; blindly adopting that build would introduce illegal instructions.
Our existing A9 build explicitly disables this definition and audits the linked
worker for unsupported instructions. Removing the definition alone does not
establish safety: fallback floating-point paths still need their context contract
checked, as do generated code and instruction-cache publication.

Useful follow-up candidates are individual compiler correctness fixes and
measured improvements to register/flag handling. Each must be compared against
our interpreter with memory-bank callbacks, executable-cache maintenance and
clean cancellation preserved. No code was imported and no speed gain is claimed.

## FS-UAE

Reviewed [FrodeSolheim/fs-uae](https://github.com/FrodeSolheim/fs-uae) at
`f362278ccd4c60991caac3b4d240d4a3f751bea2`.

The checked-out build explicitly restricts enabled guest JIT to x86/x86-64 in
`configure.ac`. ARM source files exist under `jit/`, but their presence is not
proof of a supported ARM32 JIT build. `Makefile.am` selects the x86 compiler
sources; the frontend depends on SDL3 and its companion image/font libraries.
It cannot simply be compiled and run as our bare-metal XACP worker.

FS-UAE is still a useful reference for UAE chipset fixes, configuration,
presentation and audio timing. Those should be selected by a reproducible ZZUAE
failure or profile, not imported as a wholesale frontend replacement. For current
Cortex-A9 JIT work, Amiberry/UAE4ARM is the closer starting point. For either
project, faster CPU emulation does not by itself remove drawing, blitter, audio
or host-presentation costs in chipset-heavy OCS demos.

## Retro-Amiga

Reviewed [CrownParkComputing/Retro-Amiga](https://github.com/CrownParkComputing/Retro-Amiga)
at `f80c2703866460488a16e8ced06a54378454d0e7`.

This is an Amiberry-based Android application with a Flutter frontend. Its
current app build explicitly filters out `armeabi-v7a`: the documented reason
in `app/android/app/build.gradle.kts` is the core's 4 GiB native-memory virtual
reservation, which does not fit that 32-bit Android process layout. The supported
mobile build targets ARM64. That reservation describes virtual address space,
not a requirement for 4 GiB of physical Amiga RAM.

Its setup wizard, saved machine cards and in-session disk swap interface are
useful UX references. It does not establish a faster Cortex-A9 core for ZZUAE.
Porting the Android/Flutter frontend or its current native-memory assumptions
would be a substantial platform change. Keep our Exec-owned allocation and
banked guest-memory model; consider individual core fixes only with differential
and hardware tests. No code imported, no ZZ9000 performance result claimed.
