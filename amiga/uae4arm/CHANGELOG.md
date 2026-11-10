# ZZUAE changelog

The current Beta uses runtime 0.5.7-dev and tag v0.5.7-beta.
The first package used 0.5.0-dev and tag v0.5.0-beta.
Earlier entries describe local development builds.
The product version is maintained in `version.h` and shared by the launcher,
player and build manifests. Artifact hashes distinguish rebuilds of the same
development version. Core/transport protocol identifiers remain independent.

## Unreleased — 0.6.0-dev A1200

- Enable A600 68020 interpreter USB SD boot with 2/4/8 MiB Fast RAM, FPU off.
  Correct the no-FPU exception PC so SetPatch can recover from its FPU probe.
  Keep JIT/Cyclone Fast RAM restricted. The rebuilt accelerated player uses
  72 MiB host RAM, with its existing 32 MiB executable cache and a 16 MiB heap.
- Add extra audio reserve for physical USB disk sessions: eight host blocks,
  four-block prebuffer and five-block presentation reserve. Floppy and file-HDF
  sessions retain the earlier four/two/three-block policy. PCM format and rate
  are unchanged. Gap counts improve in AGS tests; audible verification remains.

- Wait for physical USB reads using completion signals and a five-second
  timer deadline, avoiding a 20 ms polling delay on each read while guest
  audio synthesis is stalled. Physical card access remains read-only.

- Recognise USB hard disks whose RDB is in any of the first 16 sectors,
  including the AGS Classic ECS image at sector 2. Preserve checksum validation
  and read-only physical-card access.

- Add optional A600 2/4/8 MiB Fast RAM alongside 2 MiB Chip, through Zorro-II
  autoconfiguration in the compatible 68000 player. Verify all three sizes on
  hardware. Capture AmigaVision's separate `Couldn't open screen` error: its
  eight-bitplane menu requires AGA, which extra A600 Fast RAM does not provide.
- Expose A600/A1200 hard disks as **Hard disk (.hdf) → Mount…**; check size,
  alignment and RDB checksum before launch and explain unsupported containers.
  Disable IDE mounting on models without an emulated hard-disk controller.
- Verify A600/Kickstart 2.05 booting Workbench 2.0 from HDF and persisting a
  guest-written file through the changed-block journal.
  [Hard-disk setup and AmigaVision limits](HARD-DISKS.md).

- Complete exact scroll-delay caching tests inspired by Copperline. ARM/native
  checks pass, but Banshee is 2.36% slower; retain the installed player and close
  this local optimisation round. See [scroll cache](records/a1200/SCROLL-CACHE.md).

- Test preserving ARM32 NEON sprite compositing: 24,000 physical Banshee frames
  match guest state and pixels. Reversed pairs measure only +0.33–0.36%; keep
  private, with audio gaps unresolved. See [sprite NEON](records/a1200/SPRITE-NEON.md).
- Review Copperline's cached DMA plans and bounded idle scheduling as research
  references; no Copperline code imported. See [review](records/a1200/COPPERLINE-REVIEW.md).

- Separate display-decision costs and test active-only sprite DMA slot iteration.
  The candidate matches output but measures 0.76% slower in the matched Banshee
  pair; retain the installed build. See [decision costs](records/a1200/DECISION-COSTS.md).

- Profile scheduled events and scanline phases in two 6,000-frame physical
  Banshee runs. Prioritise display-state completion and line setup; retain the
  installed player. See [event costs](records/a1200/EVENT-COSTS.md).

- Test skipping BLTNASTY-only service at the zero-cycle caller. Repeated Banshee
  comparisons improve 1.68–1.83% with matching output. Wider Slam Tilt intro/table
  checks pass correctness but show no useful gain; keep the installed player
  unchanged. See [wider blitter-service tests](records/a1200/BLITTER-WIDER.md).

- Validate a private end-compilation service shortcut, then leave it unpromoted:
  physical gameplay counters show only four eligible calls. Record the dominant
  blitter-service call frequency for further profiling; see
  [special-service investigation](records/a1200/SPECIAL-SERVICE.md).

- Measure changed-palette copies and line-state clears in a separate 6000-frame
  Banshee hardware profile; retain the installed build. See
  [palette costs](records/a1200/PALETTE-COSTS.md).

- Add optional ARM-model buffer-call reporting and counter-off/on comparisons.
  Audit shared-copy versus direct output without changing the installed player;
  see [buffer audit](records/a1200/BUFFER-AUDIT.md).

- Experimental 68020/AGA A1200 profile with 2 MiB Chip RAM and PAL/NTSC timing.
- A1200 Kickstart 39.106, 40.68 and 46.143 validation.
- IDE RDB HDF selection on mounted SD/USB and local AmigaOS volumes.
- Persistent ADF/HDF changed-block writes with undo-journal recovery.
- USB/lowlevel joystick choice alongside gameport input.
- Enable hardware-tested NEON bitplane/half-width conversion and inline ChipRAM
  reads in the experimental A1200 build; retain the interpreter default.
- Correct standard PAL AGA viewport to retain all 256 active lines.
- Apply upstream's 14 MHz CPU/chipset ratio to A1200; retain earlier profiles'
  timing. Verify the actual ARM instruction cost and matching JIT/interpreter
  register, RAM and pixel results in a synthetic timing fixture.

- Add an optional four-pixel AGA palette loop: repeated Banshee gameplay tests
  improved 1.90–2.03%; a Slam Tilt loading/intro comparison improved 3.04%.
- Include the generated pixel source in the drawing object's build fingerprint,
  preventing stale incremental builds. Rebuild the optional FPU from the same base.
- Paula comparison completed without device errors; existing audio gaps remain.
  See [compositing measurements](records/a1200/COMPOSITING.md).
- Document matched PCM-production tests: larger buffers did not fix Banshee's
  sustained audio starvation. Retain existing defaults; see
  [audio pacing](records/a1200/AUDIO-PACING.md).
- Record rejected AGA idle-fetch batching experiments and separate per-application
  ZZ9000AX output tests; see [results](records/a1200/IDLE-FETCH.md).
- Add sound-enabled CPU/chipset profiling and validated private sprite-recording
  experiments; see [remaining costs](records/a1200/REMAINING-COSTS.md).
- Complete wider Slam Tilt sprite tests without a general speed gain; retain
  the installed build. Clarify displayed versus emulated frame measurements in
  the [comparison report](records/a1200/SPRITE-WIDER.md).
- Profile sprite decisions and reject slower attachment-word batching; correct
  synthetic sprite-pointer spacing and isolate diagnostic gameplay input.
  See [sprite decision results](records/a1200/SPRITE-DECISIONS.md).
- Profile bitplane spans and test three private fetch/block-setup changes; all
  match reference output but fail the performance gate. Retain the installed
  build; see [bitplane results](records/a1200/BITPLANE-SPANS.md).
- Separate per-cycle fetch, memory and output costs with timer-floor calibration.
  Reject an idle-slot dispatch guard after matched hardware tests; see
  [per-cycle results](records/a1200/CYCLE-COSTS.md).
- Test straight and shared-loop fetch inlining against matched hardware output;
  reject both slower candidates and retain installed players. See
  [fetch-loop results](records/a1200/FETCH-INLINE.md).
- Add an independent eight-plane AGA pixel oracle covering all fetch modes and
  palette banks under PAL/NTSC, with deliberate corruption rejection. See
  [AGA fetch validation](records/a1200/AGA-FETCH-ORACLE.md).
- Extend the AGA oracle with individual pixel patterns and bounded Copper colour
  transitions; ten ARM-model cases and four FMODE 3 physical checks pass; see
  [event validation](records/a1200/AGA-EVENT-ORACLE.md).

## Unreleased — optional Cyclone engine (0.5.7-dev rebuild)

- Add a separate experimental Cyclone 68000 player and launcher CPU selection;
  preserve the default engine and existing saved settings.
- Disable the FPU choice for Cyclone and report a missing optional player.
- Adapt instruction fetches to UAE memory and synchronize CPU context at events.
- Correct MOVEM odd-address exception PC handling and add ARM regression tests.
- Credit Cyclone68000 authors FinalDave and notaz; use the GPLv2 license option.

## 0.5.7 Beta (runtime 0.5.7-dev)

- Enable corrected Copper prediction and earlier audio-pressure drawing selection in the packaged compatible-68000 player.
- Preserve the Copper's two-cycle WAIT alignment and commit its state before returning. Synchronize pending Copper work on CPU custom-register access to prevent colour/list/restart ordering regressions.
- Skip drawing before an audio-pressure discard; continue CPU, Copper, Blitter and Paula emulation on every guest frame.
- State of the Art's 6,000-frame window/Paula comparison improved from 14.60 to 17.17–17.26 average displayed FPS (about 18%). Elapsed time fell from 148.73 to 138.50–138.55 seconds. Final guest state and pixels matched.
- Document the remaining coloured-tile slowdown and audio gaps. The profiled slow interval still presents about 4 FPS; the whole-demo average is not the scene's FPS.
- Add eight synthetic Copper regression cases and publish measurements. Original upstream fast-Copper shortcuts failed pixel tests and are not enabled unchanged.
- Refresh the manual ZIP, signed offline AmiPkg installer and matching source archive. JIT/FPU algorithms are unchanged.
- [Copper investigation, fixes and limitations](../../docs/amiga-uae4arm-copper-profile.md).

## 0.5.6 Beta (runtime 0.5.6-dev)

- Document the background RAM-disk usage-query stall found during Rick Dangerous testing and the confirmed cleanup remedy.
- Removing obsolete development staging reduced the largest measured completion gaps from approximately 380 ms to 88 ms windowed and 79 ms fullscreen; no gaps over 100 ms remained in either repeat. Gameplay confirmation passed.
- Flag historical hardware timings/percentage gains for controlled remeasurement; RAM-disk occupancy was not consistently controlled. Record the reported improvement in Frontier and State of the Art without inventing new FPS figures.
- Add RAM-disk troubleshooting and test-cleanup guidance to the download and installer documentation.
- Rebuild the versioned launcher and players and refresh the signed AmiPkg installer and manual ZIP. Emulation, audio, JIT and scheduling algorithms are unchanged. Installing this release does not automatically clean RAM: or fix unrelated audio issues.
- [Investigation and measurements](../../docs/amiga-uae4arm-ram-disk-stall.md).

## 0.5.5 Beta (runtime 0.5.5-dev)

- Size JIT metadata from remaining heap space to support larger RAM/two-drive profiles without exhausting the allocator.
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
