# Verification

## Development Beta installer

The installer and manual ZIP carry the same recorded executable bytes. Native
checks verified all payload hashes, valid signatures, rejection of tampered
catalogues, icons and absence of user media/signing secrets.

On the physical Amiga, the dependency preflight refused installation with the
launcher open. A fresh install and repeat install in an isolated RAM drawer
completed. AmiPkg doctor reported all 16 application files healthy; test settings,
ROM/disk and screenshot files survived the update. Existing system scanline tools
were preserved. The existing production installation was not replaced by this test.
The package uses the previously tested player; no new guest compatibility or
performance claim is made. See installer-*.log and release-build.json.

## 0.5.0-dev

- Native configuration tests passed, including saved scanline mode and command bounds.
- Native Workbench boot-block tests reject bad signatures, checksums and truncated blocks.
- ARM instruction-model checks passed all four software scanline modes in both
  P96 formats, source-frame snapshot copies, row guards, nonce rejection,
  mapping collisions, cancellation and unmapping.
- On the physical Amiga, F5 saved four complete 640 × 256, 24-bit BMPs while F9
  cycled Soft → Smooth → Hard → Off. Every Hard-mode odd row was verified black.
  F10 exited with user_exit=1, display error 0, register/MMU/cache restoration
  and owned-memory release. This 256 KiB input/capture test stopped at a guest
  loader error; it is not an Alien Syndrome compatibility result.
- A separate 512 KiB Alien Syndrome run reached its title screen, saved an F5
  screenshot with Soft scanlines and exited through F10. 1770 displayed frames
  over 77.50 seconds, including screenshot I/O; this is not a clean FPS benchmark.
- The GUI launch completed 1800 guest / 900 displayed frames and clean teardown.
  Opening and loading splashes were captured on Workbench; loading closed at
  first-frame readiness. Native ColorIcon installation verified the saved icon.
- After installing the supplied A600 ROM and Workbench 1.3 disks, the refreshed
  launcher reports all four Kickstart slots and Workbench 1.2/1.3/2.0 OK.
  The updated launcher screenshot records these file checks, not a new guest
  boot test. A600 boot/game validation remains pending.
- The installed 60,464-byte launcher adds blank rows before the ROM and
  Workbench checks. Its build manifest identifies this 0.5.0-dev rebuild.
- The bundled scanline installer preserved both existing system utilities.
  The launcher opened ZZScanlines V2.2; it was closed without Apply.
- Parent-workspace `make test-amiga-arm test-amiga` passed.

Audio delivery completed without a device error, but queue gaps remain:
1 in the GUI boot, 5 in the capture-mode exercise and 396 in the Alien title run.
These runs do not establish uninterrupted audible quality. Screenshot writes
can pause emulation/audio. Physical joystick movement acceptance remains pending.

The build manifests retain parent-workspace source names. The standalone export
uses the documented ZZUAE support paths; its launcher rebuild passed separately.
`docs/source-sha256.json` identifies the exported source rather than claiming the
historical parent paths are the current standalone layout.

## Earlier evidence

The retained `hardware-smoke.log`, `model.log`, `native.log` and
`framework-tests.log` describe the earlier 0.4.1-dev three-button build.
Badlands is an earlier bounded title capture (instruction bound at frame 1713),
not a completed 1800-frame/gameplay test. Workbench 2.0 is from 0.3.0 profile tests.
