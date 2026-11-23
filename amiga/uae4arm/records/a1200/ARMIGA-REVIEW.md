# Armiga source review

Inspected [amigagamesplus/armiga](https://github.com/amigagamesplus/armiga),
revision `5f6d69f8ac627dc083d22f83c4c50a9471500696`.
No code imported, build run or settings changed.

Armiga is a Buildroot/Linux distribution using RetroArch and PUAE for Anbernic
handhelds. Its documented H700 target is Cortex-A53/AArch64 with a Mali GPU.
ZZUAE runs ARMv7 Cortex-A9 code through XACP and a native Amiga host; the platform
and scheduling assumptions differ.

The PUAE workflow clones libretro/libretro-uae, then builds an AArch64 Unix shared
library with Cortex-A53 tuning, -O3, -ffast-math, frame-pointer omission and LTO.
It does not show a custom Cortex-A9 JIT or a replacement chipset engine.
Source: [.github/workflows/build-puae.yml](https://github.com/amigagamesplus/armiga/blob/5f6d69f8ac627dc083d22f83c4c50a9471500696/.github/workflows/build-puae.yml).

Useful investigations:

- LTO across CPU/chipset boundaries could be measured in a separate A9 build,
  preserving ABI/cache lifecycle and validating instruction/data relocations.
  No gain established. Earlier local inlining/O3 experiments did not provide a
  general benefit, so the flags alone are not evidence of an improvement.
- Core settings separate collision level, sound filtering/interpolation and
  video resolution. Armiga's defaults include playfield collisions, no sound
  interpolation and auto-lores/16-bit output. These expose quality/compatibility
  trade-offs; disabling work is not an equivalent optimisation by default.
- The launcher identifies WHDLoad archives by CRC32 and caches results using
  file metadata, allowing catalog matches after renaming. Useful for library
  usability, not emulation FPS. CRC32 is identification, not a security hash.
- Config versioning is explicit. Their documented upgrade replaces the complete
  configuration file; copying that policy would risk losing ZZUAE user settings.
  Preserve per-user settings if adopting versioned defaults.

[Core options](https://github.com/amigagamesplus/armiga/blob/5f6d69f8ac627dc083d22f83c4c50a9471500696/board/armiga/rootfs_overlay/etc/retroarch/PUAE%202021.opt),
[launcher](https://github.com/amigagamesplus/armiga/blob/5f6d69f8ac627dc083d22f83c4c50a9471500696/package/armiga-launcher/src/main.c),
[configuration documentation](https://github.com/amigagamesplus/armiga/blob/5f6d69f8ac627dc083d22f83c4c50a9471500696/RETROARCH-CONFIG.md).

Its Linux GPU/CPU governor settings and threaded RetroArch presentation cannot
be copied directly to the current single-Core1 XACP player. Study PUAE itself
for CPU/chipset improvements. Finish the pending independent AGA hardware
validation before promoting another optimisation candidate.
