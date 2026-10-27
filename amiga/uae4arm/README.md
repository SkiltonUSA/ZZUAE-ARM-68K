# ZZUAE — UAE4ARM/XACP prototype

Current development version: **0.5.4-dev**. See the [changelog](CHANGELOG.md).
The launcher and player share the version in `version.h`; both build manifests
record it. Numbering uses `major.minor.patch`: new features increase the minor
number, fixes increase the patch number, and incompatible product changes
increase the major number. Development builds use `-dev`, test releases
`-beta.1`, release candidates `-rc.1`, and stable releases have no suffix.
Release tags use `v` followed by that version (for example `v0.4.1-beta.1`).

A Cortex-A9 port of [Chips-fr/UAE4ARM](https://github.com/Chips-fr/uae4arm-rpi),
pinned to `fc1cb90afd6b5c6d9bb933d111c4c99c90f37688`.
The initial **PAL A500 / 68000 / OCS / 512 KiB chip RAM** diagnostic has booted
Workbench 1.2 on the physical ZZ9000. This is a development prototype, not a
finished interactive emulator.

The A9 runs the upstream compatible 68000 interpreter, chipset events, Copper,
Blitter, CIA, floppy emulation and drawing. The AmigaOS process stages media,
coordinates execution and presents frames. An optional live Workbench window
uses an allocated Picasso96 bitmap written by the ARM. It uses the
existing application Core1 lifecycle through
[Xanxi's XACP framework](https://github.com/Xanxi-Amiga/XACP-ZZ9000).
Firmware Core0 is not used as another application processor.

## Current scope

| Available | Pending |
|---|---|
| Bounded CPU, chipset and floppy-boot diagnostics; paced live window | Unbounded playback and fullscreen |
| Raw 880 KiB ADF; optional temporary writes in RAM | Disk swapping and persistent writes |
| Per-machine ROM selection; 256/512 KiB Kickstart | Additional ROM/profile compatibility testing |
| Native RGB565 captures; aspect-corrected 4:3 Workbench window | User resizing and fullscreen |
| Raw keyboard/mouse, port-2 joystick input and tester; Amiga+F10 exit | Physical joystick movement acceptance and broader interactive validation |
| Off / Paula direct / AHI stereo output | Listening acceptance, audio filters and interpolation controls |
| Verified Core1 register/cache/MMU restoration; machine-specific RAM/OCS/ECS | Full A1000 bootstrap, IDE/PCMCIA and RTC backends |

The Sound selector offers native Paula output or AHI unit 0, plus Off. The ARM
emulates and mixes all four guest Paula channels; the 68K delivers batched PCM.
With sound enabled, 25/30 FPS limits display work while emulation follows normal
PAL audio time. See [sound and joystick details](../../docs/amiga-uae4arm-audio.md).
Optional scripted mouse/fire/Space presses support reproducible startup checks.

The default compatible 68000 path uses interpretation. A separate development
player offers experimental 68020 JIT and a matching interpreter. The optional
ZZUAE-FPU player adds an experimental 68882 backed by Cortex-A9 VFP. Select an
accelerated CPU mode, then FPU: 68882 (experimental); the default is Off.
It uses double precision, not full 68882 extended precision, and only software
that issues FPU instructions can benefit. See the [FPU report](../../docs/amiga-uae4arm-fpu.md). See the [integration report and build steps](../../docs/amiga-uae4arm-jit-player.md).
These modes have not improved the measured startup throughput and retain audio
and timing limitations. The guarded NEON pixel converter restores every SIMD register it uses
inside a non-calling leaf. A per-frame state witness verifies D0–D31 and FPSCR.
Unavailable SIMD and smaller windows use scalar conversion. The build still
rejects FP/SIMD instructions outside the audited assembly leaves.

## Optimisation

The 68000 interpreter now batches exception-context setup across up to 256
instructions while retaining per-instruction chipset scheduling and fault handling.
The direct display path converts repeated source rows once, bypasses brightness
math with scanlines off, and uses sequential source reads at 640-pixel width.
The 0.5.3 NEON leaf adds RGB565 conversion and integer scanline dimming at
640-pixel width: matched startup throughput improved about 9.7% with scanlines
Off and 16.1% with Soft scanlines over 0.5.2. See the
[NEON results, stage profile and JIT audit](../../docs/amiga-uae4arm-neon.md) and
[earlier scalar optimisation](../../docs/amiga-uae4arm-optimisation.md).

## Development build

This currently uses the existing workspace toolchain: Podman connection
`nuflix-converter-root`, container `zzffmpeg-toolchain` with Arm Embedded GCC
15.3.1 and picolibc headers, Homebrew LLVM/lld, and the pinned Amiga cross-compiler
image from `scripts/amiga.py`. The PIC libc archive is the one prepared by
`scripts/build_uae4arm_libc.py`; it must already exist. This is not yet a
standalone toolchain installer.

```sh
python3 scripts/build_uae4arm.py
# Copy the matching soft-float libgcc archive into the private build drawer:
podman --connection nuflix-converter-root exec zzffmpeg-toolchain \
  cp /usr/lib/gcc/arm-none-eabi/15/thumb/v7-a/nofp/libgcc.a \
  /work/.context/amiga/uae4arm/libgcc.a
python3 scripts/build_uae4arm_probe.py
python3 scripts/build_uae4arm_machine.py --hardware
```

Outputs are under `.context/amiga/uae4arm/`:

- `ZZUAEProbe`: original synthetic CPU diagnostic.
- `machine/ZZUAEOCS`: synthetic chipset/framebuffer diagnostic.
- `machine/ZZUAEBoot`: bounded ROM/ADF boot diagnostic.
- `machine/ZZUAEPreview`: native Workbench viewer for a completed capture.
- `build-manifest.json`: source, archive and artifact hashes.

Build scripts prepare a private copy of the upstream source. They do not modify
the upstream checkout or deploy to hardware. Upstream copyright notices remain
in the copied source; UAE/UAE4ARM authors retain their respective credits and
licensing. Existing XACP lifecycle, memory and benchmark infrastructure is reused
from this workspace; the opcode/chipset implementation is UAE4ARM's.

## Tests and media

```sh
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/check_probe.py
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/check_machine.py
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/check_machine.py 2 --direct-live --direct-test
clang++ -fno-exceptions -Iamiga/uae4arm \
  tests/amiga/uae4arm/exception.cpp -o .context/amiga/uae4arm/exception-test
.context/amiga/uae4arm/exception-test
clang -Wall -Wextra -Werror -Iamiga/uae4arm \
  tests/amiga/uae4arm/live_plan.c -o .context/amiga/uae4arm/live-plan-test
.context/amiga/uae4arm/live-plan-test
make test-amiga-arm test-amiga
```

The model tests need Unicorn. They do not establish hardware cache behavior or
real-time performance. An optional numeric argument to `check_machine.py` runs
that many boot frames using private staged media; `1` exercises the cross-endian
frame-count request, guest button/key transitions, temporary image writes and
Paula interrupt behavior. Long model boot runs can take several minutes.

`scripts/prepare_uae4arm_media.py` extracts the 256 KiB payload from a supplied
A1000 Kickstart disk and validates ROM and Workbench boot-block checksums. Its
optional `--desktop-startup` creates a **separate** ADF with `LoadWB`/`EndCLI`,
using amitools. Original attachments are preserved. The supplied Workbench 1.2
disk has a custom diagnostic startup, so the desktop test used this separate
copy. ROMs, Workbench images and game disks are private test inputs and are not
distribution assets.

## Physical diagnostic use

The present launcher targets the verified **XX19c/XACP 1.7** setup. It requires
a Zorro III ZZ9000 with its Fast RAM enabled, a free Core1, Picasso96API and
32 MiB of suitable contiguous free board RAM. The CPU-only probe uses 8 MiB.
Tests used the A4000TX/TF4060; that is the tested host, not a claim that TF4060
is required. The 68K frontend is compiled for 68020 or later.

Stage the executable and media in RAM, then from an Amiga Shell:

```text
Stack 131072
Protect RAM:ZZUAEBoot +e
RAM:ZZUAEBoot <fresh-hex-session> RUN RAM:BootDisk.adf 1800
```

Kickstart is read from `RAM:Kick12.rom`. Optional arguments select the ADF and
frame limit (1–6000); the default disk is `RAM:WB12.adf`, with 1800 frames.
After the frame count, optional `LMB`, `FIRE` or `SPACE` sends one guest press at
rendered frame 900 and releases it at frame 910. Optional `WRITE` permits writes
to the private in-memory image only; changes are discarded on exit. Host media
is opened read-only and the supplied ADF stays unchanged. For example:

```text
RAM:ZZUAEBoot <fresh-hex-session> RUN RAM:Alien.adf 1800 WRITE LMB
```

Execution also has a 20-million-instruction bound and a 120-second host timeout.
A capture can stop at the instruction bound before reaching the frame target;
the log explicitly reports that case. It is not a successful game test by itself.

### Workbench launcher (0.5.4-dev)

Normal play offers Window, Fullscreen PAL (320×256) and Fullscreen HiRes (640×512),
and continues until stopped. Fullscreen requires the matching 32-bit RTG mode;
it does not save Workbench screen settings. Use `ZZUAE -test` or icon ToolType `TEST=YES` for bounded frame runs,
capture-only output, F5 screenshots and the diagnostic renderer. Normal mode
passes F5 to the guest. See the [current launcher guide](../../docs/amiga-uae4arm-launcher.md).
The bounded command-line examples below are diagnostics. A frame count of `0`
with `LIVE` means interactive play; append `FULLSCREEN` for PAL or `FULLSCREENHIRES`
for text at full horizontal resolution.

Build the native MUI frontend with `python3 scripts/build_uae4arm_launcher.py`.
Build its player separately with `python3 scripts/build_uae4arm_machine.py --hardware`.
Place the resulting `ZZUAE` and `machine/ZZUAEBoot` (renamed `ZZUAE-Player`)
in the same writable drawer. The launcher requires MUI 3.8 or later and AmigaOS
3.x; the direct window renderer needs a 32-bit RTG Workbench and the existing
XX19c/XACP runtime. ROMs and Workbench/game disks are supplied separately.

The reference-inspired setup window has a scrolling startup/error panel above
two aligned settings columns, ROM/DF0 file browsers, and Save / Start / Cancel.
It offers window or capture output, direct ARM or diagnostic CPU-copy rendering,
read-only or temporary DF0 writes, and bounded 500–3000-frame runs. Frame rate
choices are **25, 30, 50 and MAX FPS**. With sound enabled, PAL audio pacing
keeps guest time while 25/30 FPS skips presentation. With sound Off, the current
caps pace the whole guest. Capture output is unpaced and silent. The separate
run limit remains a total frame count.
The Machine selector offers **A1000, A500, A500 Plus and A600**. Each remembers
its own Kickstart path and updates the chipset and memory choices. A1000 offers
256/512 KiB Chip; A500 offers 512 KiB Chip with optional 512 KiB Slow RAM;
A500 Plus/A600 offer 1/2 MiB Chip. Defaults select Kickstart 1.2, 1.3, 2.04 and
2.05 respectively. CPU remains PAL 68000; ECS is selected for Plus/A600.
See [profile scope and validation](../../docs/amiga-uae4arm-profiles.md).
The A1000 starts with a preloaded Kickstart. Fullscreen remains pending.
Version 0.4.0-dev adds Paula/AHI sound; 0.4.1-dev supports three fire buttons
and a port-2 tester with oval directions and round fire indicators.

`Start` validates ROM size/checksum and ADF size, then launches a separate player.
Boot milestones, frame progress and errors appear in the top panel during the
run. The complete output remains in `Last-Run.log`. `Cancel` becomes `Stop`;
closing an active launcher waits for player shutdown. Amiga+F10 exits the active
emulation window. Only one Core1 application may run at a time.

`Save` writes `ZZUAE.cfg`; it does not change Amiga startup or display preferences.
Default ROM names are `ROMs/Kick12.rom`, `Kick13.rom`, `Kick204.rom` and
`Kick205.rom`. The initial disk is `Disks/Workbench12.adf`; disk choice is independent
of machine choice.
The optional `ROM <path>` player argument selects another ROM without replacing
the CLI default in RAM:. `ZZUAE --make-icon <executable>` and
`ZZUAE --make-drawer <drawer>` create missing Workbench icons and preserve existing
icons.

Hardware frame-rate, memory, cancellation and settings-reload results are recorded in
[the launcher report](../../docs/amiga-uae4arm-launcher.md).

### Live player

Append `LIVE` for the direct-bitmap Workbench path:

```text
RAM:ZZUAELive <fresh-hex-session> RUN RAM:WB12.adf 1800 LIVE
RAM:ZZUAELive <fresh-hex-session> RUN RAM:Alien.adf 1800 LIVE WRITE
```

`RAM:ZZUAELive` is the staged development build of `machine/ZZUAEBoot`.
It needs a **32-bit RTG Workbench**. From 0.5.1-dev, the window scales the
640 × 256 source into a 4:3 display area, up to 640 × 480. It automatically
chooses a smaller 4:3 area when Workbench is smaller (552 × 414 on 640 × 480).
Both direct ARM and copy rendering paths use this geometry. Windowed mouse input
is click-to-capture; Amiga+Esc toggles capture/release in the active window. Raw relative input continues
without moving the native pointer out of the window. Guest timing and native F5 capture size
remain unchanged. `LIVE` defaults to a 50 Hz cap when no `FPS` argument is supplied and
raises the instruction bound to 200 million; frame and bounded wall-time
limits remain in force (at least 120 seconds; extended for slower FPS caps). Slow emulation runs below the target rate; there is no
automatic frameskip. Amiga+F10, the close gadget or Ctrl-C ends a run cooperatively.

Keyboard events go to the guest; cursor keys also control joystick port 2 and
left Alt acts as its fire button. Mouse buttons/movement go to guest port 1.
Deactivating the window releases held guest inputs. Physical Amiga port-2 input is available through lowlevel.library V40. Append `FPS 25`, `FPS 30` or `FPS MAX` to select pacing; `RAM 1M` adds
512 KiB Slow RAM at guest address `$C00000` (`RAM 512K` selects the base machine).
The PAL chipset timing remains unchanged. MAX can run the guest faster than real
time. These memory choices do not establish A500 Plus/A600/ECS compatibility.

`COPY` selects the slow diagnostic
RGB565/Picasso96 transfer path instead of direct ARM rendering.

The direct path follows the proven ZZDosBox window design: allocate and lock an
offscreen P96 bitmap, validate both ends of its translated address with a nonce,
temporarily map only its pages as noncached/nonexecutable, convert on ARM, then
unmap before signalling completion. Intuition handles Workbench clipping. The
ARM never writes the Workbench screen bitmap. It can prepare the next CPU frame
while the previous bitmap is blitted, but cannot write the bitmap again until
the host grants it after `WaitBlit`. Bitmap cleanup occurs only after synchronous
Core1 reset, including error and timeout paths.

Model tests cover frame/grant/ACK ordering, stable published pixels, input,
both native pixel formats, row padding, failed ownership challenges, existing
mapping rejection and cancellation cleanup. Physical results are documented
separately in the prototype report; model success alone is not a hardware result.

Only one emulation request is made per process: reset/reuse of upstream static
state across multiple runs has not been validated. The shared allocation is
probed at runtime; observed physical addresses must never become fixed allocations.

After a successful run, `RAM:ZZUAE-Boot.rgb565` contains the final 640 × 256
little-endian RGB565 frame. `ZZUAEPreview` displays this **static capture**; its
close gadget releases the viewer. It does not keep emulation running.

See [the test report](../../docs/amiga-uae4arm-prototype.md) and
[profile/architecture review](../../docs/amiga-uae4arm-feasibility.md).

Machine CLI examples (use your own matching ROM and ADF paths):

```text
ZZUAE-Player <session> RUN <disk.adf> 1800 LIVE ROM <kick.rom> MODEL A500PLUS RAM EXPANDED FPS MAX
```

`MODEL` accepts A1000/A500/A500PLUS/A600. `RAM BASE` or `RAM EXPANDED` selects
the model-specific memory shown in the launcher. Without MODEL the older A500
diagnostic invocation remains supported. Do not mix a new launcher with an older
player: ROM staging and the shared-media layout changed together in 0.3.0-dev.

On opening, the launcher checks each configured Kickstart slot and logs `.....OK`,
`.....MISSING` or `.....INVALID`. OK means its size, checksum and profile-version
checks pass; it does not establish full game compatibility. Selecting a ROM with
Browse refreshes that slot. Missing volumes do not trigger insertion requesters.

Workbench checks look in `Disks/Workbench12.adf`, `Workbench13.adf` and
`Workbench20.adf`. OK requires 880 KiB size, a DOS boot signature and a valid
boot-block checksum; the file naming identifies the expected version, not a
complete verification of its installed files. The selected DF0 image gets an
880 KiB size check so custom game boot blocks remain accepted.

## Capture, scanlines and splash screens

F5 saves a 640 × 256, 24-bit BMP under `Screenshots` beside the player. The
ARM supplies a completed frame; the host saves it before acknowledging reuse.
Captures contain the unmodified framebuffer; FPGA scanlines are visible only on the physical output. Saving can briefly
pause emulation/audio while the file is written. Existing screenshots are not
overwritten. The startup log reports the path or a save failure.

**ZZUAE uses Xanxi’s ZZScanlines exclusively.** F9 cycles
Off → Classic → Soft → Gradient → Off in PAL fullscreen. The launcher has a
ZZScanlines On/Off switch and a saved style selector. Compatible FPGA firmware
is required. The built-in software scanline effect has been removed.

Windowed mode has no scanline effect and its selector is disabled. FPGA
scanlines affect a whole low-resolution output, not an individual Workbench
window. ZZUAE sets the mode through Xanxi’s register interface when its private
320×256 fullscreen screen opens and disables it on exit. These registers are
write-only, so a previous global setting cannot be restored by reading them.
F9 changes the current session only. Existing software-effect preferences are
mapped to the closest firmware style when loaded; the files change only on Save.

The opening splash displays the version and shortcuts. Loading remains visible
until the first completed emulation frame is presented (which may be an early
boot frame), or the run ends/fails. Its Cancel button requests a clean stop.
Amiga+F10 exits emulation. The icon and splash artwork are embedded; no image datatype
is needed. Build `ZZUAE-MakeIcon` with the launcher and run it against the ZZUAE
executable to apply the colour icon while preserving launch metadata; it uses
icon.library V44. The launcher itself does not require that helper at runtime.

When expected media is missing, the log shows the supplied reference URLs:
`https://retroroms.org` for Kickstart and `https://grandis.nu/turran/` for Workbench
TOSEC. No downloads occur automatically.

Xanxi’s original ZZScanlines utilities are bundled with source and license.
Use the Firmware / ZZScanlines button for their control panel. Existing system
copies are preferred; the bundled copies are the fallback. The optional
Install-Scanlines helper only installs missing tools. See [firmware scanlines](scanlines/README.md)
for mode/firmware requirements. High-resolution Workbench does not gain firmware
scanlines merely by opening this utility.

## 0.5.4 development work

The NEON row converter selects byte order and brightness once per row, skips
multiplication for full brightness, and hoists alpha calculation. Audio transfers
are batched before display servicing; the 64 ms AHI startup prebuffer is retained.
A600 desktop checks now include both supplied Kickstart 2.05 revisions with
Workbench 2.0. See [results and limits](../../docs/amiga-uae4arm-054.md).

`build_uae4arm_machine.py --hardware --jit-cache-test` creates an isolated cache
witness build. It executes and rewrites small ARM routines in owned private
pages, restores XN on release, and checks teardown. It is **not guest JIT** and
is excluded from normal builds. `tests/amiga/uae4arm/jit_cache.py` tests the hooks
in the instruction model; `probe_uae4arm_jit.py --cache-hooks` checks the separate
relocatable link with a bounded 512 KiB upstream cache configuration. CPU dispatch,
FP context/fault handling and guest differential tests remain unfinished.

Current development update: FPS controls and the decorative border are test-only
(`ZZUAE -test`). Normal play shows neither. See [ZZScanlines and Frontier results](../../docs/amiga-uae4arm-zzscanlines.md).
