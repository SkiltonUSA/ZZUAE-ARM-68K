# ZZUAE — Amiga OCS/ECS Emulation on ZZ9000

**0.5.3 Development Beta · Runtime 0.5.3-dev**

<img src="amiga/uae4arm/assets/zzuae-logo.png" alt="ZZUAE" width="180">

Amiga emulation on the ZZ9000 Cortex-A9, with a native AmigaOS MUI launcher.
Based on [Chips-fr/UAE4ARM](https://github.com/Chips-fr/uae4arm-rpi), using
[Xanxi’s XACP framework](https://github.com/Xanxi-Amiga/XACP-ZZ9000) for the
68K/ARM execution model.

![ZZUAE launcher](docs/screenshots/launcher.png)

## Download and install

[Download the development Beta](https://github.com/SkiltonUSA/ZZUAE-ARM-68K/releases/tag/v0.5.3-beta).
Choose the **AmiPkg LHA** for guided offline installation or the **ZIP** for manual
copying. Extract the installer, open its drawer and double-click **Install**.
Both include Xanxi’s scanline tools; supply your own ROMs and disks.
[Installation and dependency checks](docs/amiga-uae4arm-installer.md).

## Features

- A1000, A500, A500 Plus and A600 profiles, with matching OCS/ECS and memory settings.
- 68000 emulation on Cortex-A9; Copper, Blitter, CIA, floppy and Paula emulation.
- Per-machine Kickstart selection and ADF loading.
- Startup checks for Kickstart and Workbench disks, with OK / MISSING / INVALID status.
- 4:3 Workbench window, up to 640 × 480 and fitted to smaller screens, with an ARM-written Picasso96 bitmap.
- 25, 30, 50 or MAX FPS display choices; audio-paced PAL guest timing when sound is on.
- Paula direct, AHI stereo, or sound Off.
- Keyboard, mouse and Amiga port-2 joystick input; three guest fire buttons.
- Joystick tester, saved settings, startup/error log and cooperative Stop/F10 exit.
- Read-only disks or temporary writes to an in-memory copy.
- F5 screenshot capture to BMP; F9 cycles software scanlines; F10 exits.
- Bundled Xanxi ZZScanlines firmware utility, with an install-missing helper.
- Saved Scanlines On/Off switch with Soft, Smooth and Hard styles for the emulation window.
- Guarded NEON pixel conversion and scanline dimming at 640-pixel width; scalar fallback for smaller windows.
- Matching colour Workbench icon and opening/loading splash screens with shortcuts.

## Requirements

| Component | Requirement |
|---|---|
| Amiga | AmigaOS 3.x; 68020-compatible host executable |
| ZZ9000 | XX19c/XACP runtime used by this prototype; available application Core1 |
| Memory | 32 MiB available in ZZ9000 RAM for the owned runtime allocation, plus OS/UI headroom |
| Display | Picasso96 and a supported 32-bit RTG Workbench for direct window rendering |
| Launcher | MUI 3.8 or later |
| Joystick | lowlevel.library V40; available buttons depend on controller reports |
| Sound | AHI unit 0 for AHI output; native audio.device for Paula direct |
| Media | Matching Kickstart ROM and Workbench/game disk images supplied separately |

Development has been tested on an A4000TX with TF4060. The TF4060 is the tested
configuration, not a hard-coded requirement; slower host CPUs remain unmeasured.
Only one application may use Core1 at a time.

## Screenshots

Captured on the physical A4000TX/ZZ9000, with native FinalWriter running beside
ZZUAE. Badlands shows its **demo race**; Alien Syndrome shows its **title screen**.
The comparisons use software scanlines inside the game window. Click an image
for the full-size Workbench capture.

| Game | Scanlines Off | Soft scanlines |
|---|---|---|
| Badlands — demo race | ![Badlands without scanlines](docs/screenshots/badlands-multitasking-clean.png) | ![Badlands with scanlines](docs/screenshots/badlands-multitasking-scanlines.png) |
| Alien Syndrome — title | ![Alien Syndrome without scanlines](docs/screenshots/alien-multitasking-clean.png) | ![Alien Syndrome with scanlines](docs/screenshots/alien-multitasking-scanlines.png) |

### Startup and loading

| Opening splash | Loading splash |
|---|---|
| ![Opening splash](docs/screenshots/startup.png) | ![Loading splash](docs/screenshots/loading.png) |

### Three-button joystick tester

![Joystick tester](docs/screenshots/joystick.png)

### Workbench 2.0 in the A500 Plus profile

![Emulated Workbench 2.0](docs/screenshots/workbench20.png)

## Optimisation results

### 0.5.4 development update

The development branch adds about **5.3%** more startup throughput over 0.5.3:
**49.38 → 52.01 emulated FPS** with Soft scanlines in a matched Alien Syndrome run.
Audio-aware presentation reduced late queue observations **411 → 1** in a longer
run, by deferring **15% of display updates** while preserving guest CPU and PCM
results. Listening acceptance remains pending.

A600 / Workbench 2.0 desktop boots passed with both supplied Kickstart 2.05
revisions. [Audio/NEON results and evidence](docs/amiga-uae4arm-054.md).

The development launcher now offers **68000 compatible**, **68020 JIT
(experimental)** and a matching **68020 interpreter (test)**. The compatible
68000 player remains the default; guest FPU is disabled. The JIT port corrects
byte-register moves and validates modified RAM code before dispatch.

Matched Alien Syndrome startup runs show **no meaningful JIT speed gain yet**:

| Presentation | 68020 interpreter | 68020 JIT |
|---|---:|---:|
| Direct window, Soft scanlines | 49.00 emulated FPS | 48.76 emulated FPS |
| No live window | 68.97 emulated FPS | 69.03 emulated FPS |

These are single 1,800-frame startup comparisons, not sustained gameplay FPS.
Longer experimental runs still show audio scheduling issues and divergent game
state; use **68000 compatible** for normal play.
[JIT integration, correctness fixes and test evidence](docs/amiga-uae4arm-jit-player.md).
The downloadable Beta remains **0.5.3**; experimental JIT is development-only.

### NEON renderer (0.5.3)

Matched 1,800-frame Alien Syndrome startup runs, Direct 640 × 480, audio Off
and MAX frame rate on the A4000TX/ZZ9000:

| Scanlines | Scalar baseline | NEON | Throughput gain |
|---|---:|---:|---:|
| Off | 45.02 emulated FPS | 49.39 emulated FPS | +9.7% |
| Soft | 42.62 emulated FPS | 49.48 emulated FPS | +16.1% |

Guest instruction counts, cycles, final PC and frame hash matched. These measure
startup/title emulation throughput, not sustained gameplay FPS. Off uses the
mean elapsed time of two NEON runs.

With AHI audio and a 25 FPS display cap, a separate 3,000-frame run fell from
63.24 to 60.60 seconds; late audio-queue observations fell from 334 to 34.
PCM delivery completed without device errors; listening acceptance remains pending.
The assembly preserves SIMD state, with scalar fallback when NEON is unavailable.
[Full measurements, stage profiling, validation and JIT investigation](docs/amiga-uae4arm-neon.md).

### Earlier interpreter and renderer work (0.5.2)

Matched 1,800-frame Alien Syndrome startup runs on the A4000TX/ZZ9000,
640 × 480 Direct window, audio Off, scanlines Off and MAX frame rate:

| Build | Mean emulated FPS | Gain over baseline |
|---|---:|---:|
| 0.5.1 baseline | 29.17 | — |
| Batched interpreter exception context | 30.24 | +3.69% |
| Plus cached converted rows and specialised pixel loops (0.5.2) | 44.99 | +54.24% |

Guest instructions, cycles, final PC and frame hash matched. These are uncapped
startup measurements, not gameplay FPS or a promise of full-speed compatibility.
That earlier pass added no JIT, NEON or VFP; NEON was introduced in 0.5.3. [Method, audio results and validation](docs/amiga-uae4arm-optimisation.md).

## Current Beta Status

A1000, A500, A500 Plus and A600 desktop boot checks passed on hardware.
A600 tests used Kickstart 37.350 with 1 MiB and 37.300 with 2 MiB Chip RAM,
plus Workbench 2.0. General A600 game/peripheral compatibility remains pending.
The A1000 profile
uses a preloaded ROM rather than the original disk-bootstrap sequence.

This is a bounded prototype: fullscreen, unlimited play, disk swapping,
persistent disk writes, IDE/PCMCIA media and RTC backends remain unfinished.
Audio queue gaps are still being investigated; listening and physical joystick
acceptance remain pending. With sound Off, current frame caps also slow guest time.
NEON accelerates the 640-pixel display path. The development-only JIT player
emulates a 68020 and has passed bounded game and Workbench boot checks; wider
compatibility and self-modifying-code coverage remain unfinished. Guest FPU is
disabled. The downloadable Beta retains the compatible 68000 interpreter.

ZZScanlines requires compatible FPGA firmware and a supported low-resolution
mode. High-resolution RTG Workbench is normally unaffected; ZZUAE’s optional
software scanlines work inside its window. Opening the firmware utility does
not automatically alter the display.

## Development

- [Build instructions and implementation](amiga/uae4arm/README.md)
- [Standalone backup/build scope](docs/BUILD.md)
- [Changelog](CHANGELOG.md)
- [Bundled ZZScanlines](amiga/uae4arm/scanlines/README.md)
- [Sound and input](docs/amiga-uae4arm-audio.md)
- [Machine profiles](docs/amiga-uae4arm-profiles.md)
- [Live rendering measurements](docs/amiga-uae4arm-live.md)
- [Initial prototype and SysInfo results](docs/amiga-uae4arm-prototype.md)
- [Verification records](docs/verification/README.md)
- [Credits and licensing](NOTICE.md)

The core is pinned to `fc1cb90afd6b5c6d9bb933d111c4c99c90f37688`.
The shared version lives in `amiga/uae4arm/version.h`.

Development: Codex assisted, Amiga-Bridge MCP.
