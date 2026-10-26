# ZZUAE changelog

Development versions below describe local builds, not published releases.
The product version is maintained in `version.h` and shared by the launcher,
player and build manifests. Artifact hashes distinguish rebuilds of the same
development version. Core/transport protocol identifiers remain independent.

## 0.5.0-dev

- Bundled Xanxi ZZScanlines utilities and an install-missing helper; launcher opens system or bundled control panel.
- Startup credits and aligned media-check columns in the dialog log.
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
