# ZZUAE — UAE4ARM/XACP prototype

Current version: **0.4.1-dev**. See the [changelog](CHANGELOG.md).
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
| 320/640 × 256 RGB565 captures; live 640 × 256 window | Aspect correction and resizing |
| Raw keyboard/mouse, port-2 joystick input and tester; F10 exit | Physical joystick movement acceptance and broader interactive validation |
| Off / Paula direct / AHI stereo output | Listening acceptance, audio filters and interpolation controls |
| Verified Core1 register/cache/MMU restoration; machine-specific RAM/OCS/ECS | Full A1000 bootstrap, IDE/PCMCIA and RTC backends |

The Sound selector offers native Paula output or AHI unit 0, plus Off. The ARM
emulates and mixes all four guest Paula channels; the 68K delivers batched PCM.
With sound enabled, 25/30 FPS limits display work while emulation follows normal
PAL audio time. See [sound and joystick details](../../docs/amiga-uae4arm-audio.md).
Optional scripted mouse/fire/Space presses support reproducible startup checks.

No JIT, NEON or VFP is enabled in this baseline. The compatible upstream 68000
path uses interpretation. The integer-only context helpers deliberately reject
linked VFP/NEON instructions during the build. Enabling those instructions later
requires a corresponding context-preservation implementation and new tests.

## Development build

This currently uses the existing workspace toolchain: Podman connection
`nuflix-converter-root`, container `zzffmpeg-toolchain` with Arm Embedded GCC
15.3.1 and picolibc headers, Homebrew LLVM/lld, and the pinned Amiga cross-compiler
image from `scripts/amiga.py`. The PIC libc archive is the one prepared by
`scripts/build_pocketsnes_libc.py`; it must already exist. This is not yet a
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

### Workbench launcher (0.4.1-dev)

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
closing an active launcher waits for player shutdown. F10 exits the active
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
It needs a **32-bit RTG Workbench**. The window currently displays the original
640 × 256 capture geometry without aspect correction. `LIVE` defaults to a 50 Hz cap when no `FPS` argument is supplied and
raises the instruction bound to 200 million; frame and bounded wall-time
limits remain in force (at least 120 seconds; extended for slower FPS caps). Slow emulation runs below the target rate; there is no
automatic frameskip. F10, the close gadget or Ctrl-C ends a run cooperatively.

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
