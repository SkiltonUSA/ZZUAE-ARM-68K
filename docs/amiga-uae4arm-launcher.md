# ZZUAE Workbench launcher

## Normal play and testing — 0.5.4-dev

Normal launches offer **Window**, **Fullscreen PAL** (320×256) and
**Fullscreen HiRes** (640×512), and run until F10, Stop or window close.
The 25/30/50/MAX frame-rate setting controls pacing/presentation.

PAL is intended for games. HiRes preserves all 640 horizontal source pixels
and doubles each of the 256 source rows evenly, improving text presentation.
Both open temporary 32-bit RTG screens and require a matching installed mode.
Window mode uses 4:3 scaling up to 640×480, fitted to Workbench. Select a display
mode before Start; switching during a session is not implemented. Workbench
ScreenMode preferences are never saved or modified.

The FPS counter and decorative border are available only in testing mode.
The counter measures completed display presentations, not guest CPU speed.
In a window, click inside to capture the mouse; **F8** releases it to Workbench.
Only the guest pointer remains visible while captured. **F10** exits.
[Mouse input and text-resolution repair](amiga-uae4arm-mouse.md).

For diagnostic controls, run `ZZUAE -test` from Shell, or add `TEST=YES` to the
application icon's ToolTypes in Workbench Information. Remove that ToolType to
return to normal mode. The icon includes a disabled `(TEST=YES)` hint; remove
the parentheses to enable it. Testing exposes the total-frame limit, Capture only and
CPU-copy renderer. Capture-only runs have no display or sound. Test mode itself
is not saved in ZZUAE.cfg; older output/limit settings cannot force a normal
launch back into capture-only or bounded operation.

F9 cycles Xanxi ZZScanlines in low-resolution PAL fullscreen; F10 exits in every mode.
Windowed and HiRes scanlines are disabled. The FPGA effect is turned off on exit. F5 screenshot
capture and the final RAM: RGB565 capture are diagnostic-only. In normal play F5
is passed to the emulated Amiga, and the splash omits the capture shortcut.

Normal runs keep bounded CPU batches and cooperative cancellation. Diagnostic
runs retain frame, instruction and wall-time bounds. An interactive Stop has a
separate five-second response deadline; mandatory Core1 reset precedes display
and allocation release on every exit path.

The sections below record earlier milestones and their then-current limits.

## Sound and joystick update — 0.4.0-dev

Sound now offers Off, Paula direct and AHI. Joystick selects Off or Amiga port 2;
Joystick test opens a live direction/fire indicator window. Both selections are
saved. AHI uses the existing unit 0 configuration; Paula direct uses native audio
sockets. With audio enabled, 25/30 FPS reduces presentation frequency without
slowing the PAL guest or changing audio pitch. See
[implementation and verification](amiga-uae4arm-audio.md).

## Launcher

Version 0.4.0-dev implements the supplied classic setup-window reference using
native MUI: a large scrolling boot/error panel, two aligned settings columns,
ROM and DF0 file requesters, status row, and Save / Start / Cancel controls.
The available settings describe the bounded prototype. The Machine selector
automatically applies the ROM path, RAM choices and OCS/ECS settings; see
[the profile report](amiga-uae4arm-profiles.md). Normal play supports window
or fullscreen and runs until stopped.

Frame rate offers 25, 30, 50 and MAX FPS; new 0.5.4-dev settings default to 30. With sound Off, MAX is uncapped and
lower settings pace the whole lockstep guest. With sound enabled, PCM playback
paces guest time; the compatible player skips drawing frames outside the
25/30 FPS cadence while keeping CPU/chipset/Paula execution intact. An audio
reserve check can defer further display updates. 50/MAX selects every guest
frame for drawing. The experimental JIT player retains its prior drawing path. Capture-only mode ignores the display cap and disables sound.
The total-frame run limit remains separate.

Machine-specific memory ranges from 256 KiB Chip on A1000 to 2 MiB Chip on
A500 Plus/A600. A500 additionally offers 512 KiB Slow RAM. Mapped banks are
checked before guest boot. Per-machine ROM paths are persisted by Save.

## Startup and shutdown

The GUI validates media before creating a worker process. The worker invokes a
separate player synchronously while MUI continues handling events. A timer polls
the shared startup log every 250 ms. The player uses unbuffered output; the GUI
shows readable boot milestones and errors and retains the full `Last-Run.log`.
The on-screen list keeps the most recent 200 lines. Direct rendering reports
progress every 250 displayed frames; this is not an FPS measurement.

Each run has a unique public control port. Stop targets that session, never an
arbitrary ARM process. It retries only until the session port exists, sends one
cooperative Ctrl-C signal, and waits for player completion. Both executables
override libc's automatic Ctrl-C abort so output routines cannot bypass explicit
cleanup. The shared Core1 launcher, mapping checks and reset-before-free contract
remain unchanged.

## Verification on 26 October 2026

- Native configuration tests passed with AddressSanitizer and UndefinedBehaviorSanitizer:
  save/load round trip, transactional rejection of invalid settings, Shell quoting,
  command bounds and output selection.
- M68k launcher and player builds passed with warnings treated as errors.
- `make test-amiga-arm test-amiga` passed, including MCP smoke checks.
- Physical MUI window opened at 620 × 430. Layout and disabled controls were
  captured. Workbench drawer and application icons were created.
- Start launched the selected persistent ROM and ADF. The top panel showed actual
  startup milestones while the player was running, then 250/500/750-frame progress.
- The first Stop test ended guest execution at frame 852, but repeated Ctrl-C
  delivery triggered libc `***Break` during restoration logging. It returned 20
  and left session resources allocated. This is a failed shutdown test, not a pass.
- The correction sends Stop once and disables libc's asynchronous abort in both
  executables. A reboot was requested to clear the stale resources. Corrected
  Stop and repeated-run retests subsequently passed after reboot (see below).
  File-requester interaction is not part of that acceptance.

Raw first-run evidence and build records are in
`amiga/records/2026-10-26/uae4arm/launcher/`. Screenshots are private under
`.context/amiga/uae4arm/launcher/`.

## Installation

Installed in `SD032G:Emulator/ZZUAE`, alongside the other emulators. The drawer
contains `ZZUAE`, `ZZUAE-Player`, Workbench icons, `ROMs/` and `Disks/`. Media was
copied from existing private test files; it is not part of source or release
assets. This installation does not change firmware, startup or saved resolution.

Open ZZUAE, choose media, and use a bounded run. The complete log records
MMU/cache witnesses, synchronous Core1 reset and owned-memory release.

## Frame-rate and memory follow-up

The Amiga was restarted and the bridge reconnected; stale Core1 ports were
confirmed absent. Updated GUI/player transfers were CRC verified. Native
configuration and pacing tests passed, including microsecond-clock wrap and
timeout bounds. The actual ARM instruction model passed the 512 KiB Slow RAM
pattern/alias check and a one-frame boot, plus input and private disk-write tests.

The bridge temporarily stopped answering during an injected memory-selector
mouse click, before emulation began. A physical mouse release restored access.
Subsequent physical tests passed:

| Setting | Displayed frames | Host interval | Average displayed FPS |
|---|---:|---:|---:|
| 25 FPS | 500 | 20.752 s | 24.09 |
| 30 FPS | 500 | 17.417 s | 28.71 |
| MAX FPS | 500 | 7.268 s | 68.80 |

All three used the same private Workbench 1.2 startup disk, direct bitmap path
and 512 KiB Chip + 512 KiB Slow configuration. The interval is the player's
`LIVE elapsed_us`, including final capture overhead; these are short startup
measurements, not game FPS or guaranteed sustained rates. Each run reported
`MEMORY chip=524288 slow=524288 verified=1`, zero register mismatches, zero cache
witness errors and successful memory release. Core1 ports disappeared afterward.

A separate run started through the GUI and stopped with its Stop button after
395 guest frames. It returned success, recorded `user_exit=1`, restored the
ARM state and released all owned memory. The earlier cancellation fault is
resolved in this tested build. Save wrote the selected 1 MiB/MAX settings.
Evidence: `amiga/records/2026-10-26/uae4arm/fps-memory/`.

Closing and reopening the GUI restored the saved 1 MiB/MAX configuration. A
subsequent Start completed all 1800 guest frames, reached the Workbench 1.2
desktop (verified from the final RGB565 capture) and returned success with all
restoration/release checks passing. Average displayed rate was 56.27 FPS for
that longer run, including screenshot activity; do not compare it directly with
the shorter 500-frame timings. The launcher was left open with Core1 free.

Final guest capture: `.context/amiga/uae4arm/launcher/workbench-1mb-final.png`.

## Experimental guest FPU

Select **68020 JIT (experimental)** or **68020 interpreter (test)**, then
**FPU: 68882 (experimental)**. This uses the optional `ZZUAE-FPU` player.
FPU Off keeps the existing players; selecting 68000 disables the FPU control.
Save persists the selection, while Start uses it for the current launch.

The A9 VFP executes the arithmetic behind the emulated FPU. This double-precision
backend is not a full extended-precision 68882 implementation. Software must
issue FPU instructions to benefit; enabling it cannot accelerate integer-only
game calculations. [Implementation and validation](amiga-uae4arm-fpu.md).
