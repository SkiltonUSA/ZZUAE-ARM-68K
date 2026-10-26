# UAE4ARM on the physical ZZ9000 — initial prototype

Follow-up: [live window, direct bitmap rendering and input transport](amiga-uae4arm-live.md).
The sections below retain the earlier offscreen baseline; they do not describe
the later live-window measurements.

26 October 2026. Upstream revision
`fc1cb90afd6b5c6d9bb933d111c4c99c90f37688`.

**Workbench 1.2 reached its desktop on the A4000TX's Cortex-A9.** The build is
a bounded A500/OCS diagnostic, with a captured framebuffer rather than continuous
display. Live input, speaker output and sustained gameplay compatibility are not yet
established. Later builds retain Paula interrupts and add scripted guest input
and temporary image writes for startup testing.

## Verified execution

| Test | Result |
|---|---|
| Original CPU fixture, ARM model at two relocation bases | Register/memory/flag checks and cancellation passed |
| Same fixture on physical Core1 | 26,000 instructions / 234,000 guest cycles; measured samples 5,052–5,056 µs |
| Active-work cancellation in CPU probe | Passed; total test elapsed 134,486 µs |
| OCS synthetic color write | 100,000 instructions; final PC `0x108`; all 320 × 256 pixels `0xf800` |
| Physical versus model OCS frame | Byte-identical |
| Kickstart 1.2 + supplied disk, 150-frame run | White startup screen; physical/model counts, PC and hash matched |
| Supplied disk, 600-frame run | AmigaDOS Release 1.2 startup CLI rendered |
| Separate desktop-startup disk, 1800-frame run | Workbench desktop and disk icon rendered |
| Workbench capture viewer | Captured ARM frame displayed in a native AmigaOS window |

The CPU fixture exercises five upstream opcode handlers repeatedly. It is not a
complete 68000 conformance suite. The physical chipset test covered the original
synthetic color-register program, not every Copper/Blitter/sprite mode.

The final 1800-frame desktop run completed in **19.662 seconds**, including the host's
completion polling. That is approximately **91.5 offscreen rendered frames/s**
for this boot/desktop workload. It excludes live frame presentation, audio and
input; it is **not a gameplay FPS or sustained compatibility claim**. Its
4,464,947 explicitly stepped instructions and 50,502,188 counted instruction
cycles do not include chipset cycles advanced inside CPU STOP handling.

The 32-bit ARM tick field wraps during this longer run. Its raw value must not be
converted into elapsed time without accounting for wrap; the reported duration
uses the host timer around the request instead.

All completed physical diagnostics restored the checked registers, CPSR control,
MMU/cache state and cache witness, returned through RET1, synchronously reset
Core1 to idle and released their Exec allocation. No firmware, saved Workbench
display mode, startup configuration or existing emulator installation was changed.

## SysInfo 1.98 on the physical A9

The supplied SysInfo 1.98 ADF was tested inside the same PAL A500/68000 profile,
using Kickstart 1.2. A private copy replaced only `s/startup-sequence` to bypass
the magazine menu. All other 47 file contents and the original attachment were
preserved. Neither test executed SysInfo natively on the host's 68060.

| Measurement | Observed result |
|---|---|
| SysInfo version shown | 1.98 |
| Guest CPU identification | 68000; no FPU or MMU |
| Guest CPU speed estimate | 7.27 MHz |
| SysInfo A500 STANDARD comparison | 1.33× |
| Internal `-t` results | Speed 344 ticks; MHz 238 ticks; rating 256 ticks |
| Timed CLI boot/test/capture workload | 1800 frames in 21.032851 s; 85.58 offscreen frames/s |
| Normal GUI boot/test/capture workload | 1800 frames in 22.104022 s; 81.43 offscreen frames/s |

These are two different workloads, not repeated samples of one benchmark.
Both reached the requested frame limit, restored the checked register/cache/MMU
state, reset Core1 and released the allocation. The CLI test returned to its
prompt; the GUI displayed its completed results.

The guest MHz and comparison figures use emulated timing. They are **not the
Cortex-A9's MHz or a native ARM benchmark**. In particular, the 1.33× comparison
does not establish cycle-exact stock A500 timing; CPU/chipset contention accuracy
still needs independent validation. The current compatible interpreter keeps
CPU and chipset scheduling coupled but is not the upstream cycle-exact CPU path.

At a nominal 50 Hz PAL rate, the 1800-frame workload represents approximately
36 seconds of guest video time. Completing it in 22.10 seconds demonstrates
about 1.63× real-time throughput for this boot/benchmark/idle mixture. It does
not establish a steady benchmark-loop rate, gameplay FPS, or the throughput
after live presentation and audio are added. No MIPS figure was displayed by
this version, so none is inferred from the comparison ratio.

Raw logs and media hashes: `amiga/records/2026-10-26/uae4arm/sysinfo-*`.
Private captures: `.context/amiga/uae4arm/sysinfo/supplied-198.png` and
`supplied-198-gui.png`. CLI switch behavior is also described in the
[SysInfo guide](https://sysinfo.d0.se/guide/usagecli); the supplied 1.98 binary
was the version actually executed. The separately downloaded 3.24 was not used.

## Supplied media

All ten initial images were inspected. The six Kickstart disks contain 256 KiB
payloads at offset 512 with valid ROM checksums. The four Workbench inputs are raw
880 KiB DOS0 ADFs; the `.man` extension does not change their format.

Selected clean ROM: **Kickstart 1.2 revision 33.166**, extracted from the supplied
A1000 disk. Running that ROM in an A500 profile does not establish accurate A1000
boot-ROM/writable-control-store emulation. No Kickstart 2.x ROM was supplied.

The supplied Workbench 1.2 disk's startup script invokes a custom diagnostic
suite. The desktop test used a private copy with only `s/startup-sequence`
replaced by `LoadWB` and `EndCLI`; an exhaustive file-content comparison confirmed
all other 140 files were unchanged. The original attachment remains untouched.

Checksums, exact run logs, captures and build receipts are retained under
`.context/amiga/uae4arm/`. No ROM or disk image is included with source or releases.

## Initial game boot pass

The eight supplied ADFs are 880 KiB images with valid boot-block checksums. Tests
used the same A500/OCS profile and Kickstart 1.2. These are the supplied modified
variants, not a general compatibility statement for every edition of each game.

| Supplied title | Initial captured result |
|---|---|
| Batman: The Caped Crusader | Uniform dark blue; startup unresolved |
| Balance of Power: 1990 Edition | Crack intro text |
| Badlands | Complete game title screen |
| Army Moves | Defjam/CCS intro |
| Alien Syndrome | Startup explicitly requests write access; Protect command fails |
| Backlash | HQC/Champs intro |
| Beyond the Ice Palace | CBC/The Band intro |
| Bionic Commando | Intro graphics/scroll; visual correctness not yet established |

All eight initial runs restored state and released memory. Badlands reached the
20-million-instruction bound after 1713 rendered frames; the other seven reached
1800. This pass used no scripted input and disabled Paula emulation. The later
interrupts-only mode is a compatibility correction, not an established speed gain.

### Follow-up checks

With Paula interrupts retained and temporary writes enabled, **Alien Syndrome
reached its game title screen**. The original ADF remained unchanged. The initial
Protect failure was therefore a limitation of the read-only test configuration.

Batman remained byte-identical dark blue after the scripted Space press and Paula
interrupt correction. Balance of Power remained on its intro after LMB; Badlands
remained on its title after fire. These presses were scheduled at frame 900 and
released at 910; they do not establish that the game was ready to accept input at
that moment. Continuous interaction and later loading transitions remain pending.

The current visual tally is **two game titles, five intros and one unresolved
blank screen**. No title has yet passed full gameplay, sound or live-controller
acceptance. All follow-up runs returned cleanly with restoration checks passing.

## Integration findings

- Replaced Linux rendering threads with synchronous upstream drawing calls on
  application Core1; preserved emulated chipset event scheduling.
- Replaced host filesystem access with a bounded in-memory, read-only ADF backend.
- Kept the runtime-probed XACP allocation and existing restoration/teardown path.
- Adapted upstream integer bus exceptions without C++ runtime unwinding.
- Found a linked libc `setjmp` that used VFP. Replaced it with an integer-only
  context helper for this soft-float baseline. The build now rejects VFP/NEON and
  unsupported hardware-divide instructions before packaging.
- Fixed a cross-endian frame-option error: the 68K control protocol uses big-endian
  fields, while ARM framebuffer pixels use little-endian RGB565. Those formats
  must not be conflated.

- The initial `produce_sound=0` setting also disabled Paula interrupts. Changed
  it to upstream `interrupts` mode (`produce_sound=1`), retaining channel/DMA
  behavior without speaker output. The ARM model verifies that a manual audio
  word raises the channel interrupt.
- Added optional guest-only scripted LMB/fire/Space transitions, with model checks
  for active-low CIA button bits and keyboard press/release codes.
- Added optional temporary ADF writes. Model write/read checks verify that the
  staged original image remains unchanged; persistent saves are not implemented.

## Remaining development

1. Establish game boot/title captures, then test input, loading transitions and
   sustained gameplay separately.
2. Add live windowed/fullscreen presentation and one pacing authority.
3. Integrate keyboard, mouse, joystick and batched Paula/AHI audio.
4. Validate A500 Plus/ECS, A600-specific behavior and A1000 boot handling, with
   suitable ROM revisions. Implement disk selection/swapping and reset lifecycle.
5. Profile actual gameplay before enabling NEON or changing execution/cache policy.

Build/run details are in [the prototype README](../amiga/uae4arm/README.md).
