# ZZUAE changelog

The current Beta uses runtime 0.5.5-dev and tag v0.5.5-beta.
The first package used 0.5.0-dev and tag v0.5.0-beta.
Earlier entries describe local development builds.
The product version is maintained in `version.h` and shared by the launcher,
player and build manifests. Artifact hashes distinguish rebuilds of the same
development version. Core/transport protocol identifiers remain independent.

## 0.5.5 Beta (runtime 0.5.5-dev)

- Add optional host-synchronised RTC with matching clock chips and On/Off launcher control.
- Add optional DF1 ADF selection, Browse/Eject and saved settings for a second floppy drive.
- Flash independent DF0/DF1 red read lights beside the green running light in window mode.

- Package the corrected event-bounded 68020 JIT with a 32 MiB executable cache; accelerated players require 64 MiB free ZZ9000 RAM.
- Combine MOVW/MOVT constants, A9 bitfields, precomputed opcode classification, expanded register groups and early drawing/audio-pressure decisions.
- Batch exception-context setup while preserving per-dispatch events, interrupt checks, faults and cancellation.
- Measure Alien Syndrome window/AHI throughput 75.95 → 69.99 seconds for 3,000 guest frames: +8.52% against the earlier corrected JIT baseline. This is not a gameplay-FPS comparison with 0.5.4.
- Rebuild the optional VFP-backed FPU player against the same corrected core and cache configuration.
- Update launcher memory guidance, installer requirements, build records and signed offline/manual packages.
- Add 800 native dispatcher comparisons and 64 MiB lifecycle coverage; retain CPU, chipset, PCM and state-restoration checks.
- Keep compatible 68000 as the default. JIT/FPU remain experimental; the earlier long audio timeout and listening acceptance remain unresolved.
- [Combined measurements and verification](../../docs/amiga-uae4arm-jit-batch.md), [service profiling](../../docs/amiga-uae4arm-jit-service.md), [cache investigation](../../docs/amiga-uae4arm-direct-ram.md).

## 0.5.4 Beta (runtime 0.5.4-dev)

- Reserve Amiga+F10 for exit and Amiga+Esc for window mouse capture/release (either Amiga key). Plain F10, Esc and F8 now reach the guest, including Alien Syndrome’s F10 start control. Update splash/window help.

- Add two tiny window status lights outside the guest image: green for running, red for DF0 activity.

- Add Fullscreen HiRes (640×512) for text: retain all 640 horizontal samples and double each source row evenly. Keep PAL 320×256 for games; FPGA scanlines remain low-resolution only.

- Add window click-to-capture mouse control, one visible pointer and Amiga+Esc release; use Amiga+F10 to exit. Release capture on focus loss, overflow and shutdown.
- Fix stalled mouse movement by restoring the guest input-frame clock.
- Use relative host mouse events so movement continues at display edges, with consistent sensitivity across display sizes.

- Add optional ZZUAE-FPU player and launcher Off / 68882 (experimental) selection for accelerated 68020 modes.
- Execute guest FPU arithmetic through Cortex-A9 VFP; retain double-precision backend limits and integer-JIT fallback for FPU instructions.
- Preserve D0–D31/FPSCR across normal, cancelled and failed runs; report guest FPU instruction counts and restoration checks.

- Move FPS controls and decorative borders into -test mode only.
- Replace software scanlines with Xanxi ZZScanlines exclusively in PAL fullscreen.
- F9 cycles Off / Classic / Soft / Gradient; windowed controls are disabled.
- Disable the global FPGA effect on exit; migrate older saved styles on load.
- Preserve full-brightness display/capture pixels; no software dimming fallback.


- Normal play runs until stopped; frame limits and capture controls move to `-test` / `TEST=YES`.
- Add Window / Fullscreen selection using a temporary 640 × 480 RTG screen.
- Reserve F5 and final-frame file capture for diagnostic runs; normal F5 reaches the guest.
- Preserve bounded CPU dispatch and cancellation across long-running counter wrap.

- Specialise NEON row loops for brightness and pixel byte order; hoist invariant alpha work.
- Drain bounded audio batches before display servicing; retain the two-block prebuffer.
- Defer bounded display updates when audio reserve is low; matched long-run late queue observations fell from 411 to 1, with 15% fewer display updates.
- Further matched startup throughput gain of about 5.3% over 0.5.3 with Soft scanlines.
- Verify A600 / Workbench 2.0 desktop boot with Kickstart 37.350 (1 MiB) and 37.300 (2 MiB).
- Add experimental owned executable-cache hooks and actual ARM rewrite/publication tests; guest JIT remains disabled.

## 0.5.3-dev

- Guarded NEON RGB565 conversion and scanline dimming for 640-pixel windows; scalar fallback for smaller windows or unavailable SIMD.
- Leaf assembly restores all touched SIMD registers; per-frame D0–D31/FPSCR verification and render counters.
- Optional stage profiler and isolated JIT compilation audit; neither enables guest JIT or guest FPU support.
- Matched hardware startup throughput improved about 9.7% with scanlines Off and 16.1% with Soft scanlines. Longer audio run reduced queue-gap observations from 334 to 34; listening acceptance remains pending.

## 0.5.2-dev

- New development Beta installer/manual packages with multitasking screenshots, with and without software scanlines.

- Separate Scanlines On/Off switch and saved style selector; both splash screens list the F9 scanline choices.

- Batch interpreter exception-context setup across up to 256 instructions; preserve guest cycle, prefetch, interrupt and fault handling.
- Convert vertically repeated display rows once in cached ARM memory.
- Specialise 640-pixel source reads, pixel byte order and scanline brightness outside pixel loops.
- Add fault/bounds tests, exhaustive RGB565 conversion checks and ARM guest-state/audio comparison reports.
- Keep the existing integer-only worker, bitmap ownership and reset-before-free contracts.

## 0.5.1-dev

- Workbench display area now uses 4:3 proportions, up to 640 × 480, fitting smaller screens automatically.
- Direct ARM and copy rendering scale the original frame without changing guest timing.
- Mouse movement follows the scaled image; native F5 screenshot dimensions are unchanged.

## 0.5.0-dev

- First development Beta release: offline AmiPkg installer and matching manual ZIP.
- Installer checks dependencies, preserves user media/settings, and installs missing scanline tools.

- Bundled Xanxi ZZScanlines utilities and an install-missing helper; launcher opens system or bundled control panel.
- Startup credits and aligned media-check columns in the dialog log, with blank rows separating ROM and Workbench checks.
- F5 captures the held game frame to a 24-bit BMP in Screenshots beside the player.
- Software scanlines adapted from ZZDosBox: Off, Soft, Smooth and Hard; F9 cycles them.
- Saved launcher scanline setting, applied by the ARM during presentation.
- Matching colour Workbench icon and startup/loading splashes with keyboard shortcuts.
- Loading splash closes on first-frame acknowledgement, cancellation or failure.
- Missing-media startup hints show the supplied RetroRoms and Turran URLs.

## 0.4.2-dev

- Startup checks Workbench 1.2/1.3/2.0 disk slots and the selected DF0 image.
- Startup log checks all four configured Kickstart slots: OK, MISSING or INVALID.
- OK requires the expected size, checksum and machine version checks to pass.
- Missing volumes do not open disk-insertion requesters during the startup check.
- Browsing to a ROM refreshes its status.
- Launcher description: Amiga OCS/ECS Emulation on ZZ9000.

## 0.4.1-dev

- Three guest fire buttons, with physical availability determined by the
  controller and `lowlevel.library` reports.
- Oval direction indicators and circular fire indicators in the joystick tester.
- Corrected reversed left/right input mapping.
- Input checks cover all directions, three fire buttons and focus-loss release.
- Unified launcher/player version metadata; removed the player's stale
  `0.1-dev` label.
- Physical 120-frame boot and clean shutdown passed. Physical button testing
  and audio listening acceptance remain pending.

## 0.4.0-dev

- Off, Paula direct and AHI sound choices with batched stereo PCM playback.
- Audio-paced PAL emulation; 25/30 FPS limits presentation when sound is enabled.
- Amiga port-2 joystick input and a launcher joystick tester.
- Saved sound/input selections and cooperative Start/Stop handling.
- Audio queue gaps remain under investigation.

## 0.3.0-dev

- Machine-specific A1000, A500, A500 Plus and A600 profiles.
- Per-machine Kickstart selection, matching chipset settings and memory choices.
- Revised ROM staging and shared-media layout; launcher and player must be
  updated together.

Earlier prototype work is described in the development reports. No additional
release numbers are assigned retrospectively.
