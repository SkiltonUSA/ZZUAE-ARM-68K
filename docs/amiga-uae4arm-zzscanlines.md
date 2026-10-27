# ZZUAE: Xanxi ZZScanlines only

The 0.5.4 development player now uses Xanxi’s FPGA scanline interface exclusively.
The native PAL fullscreen is 320×256. F9 cycles Off, Classic, Soft and Gradient.
The launcher saves an On/Off switch and style; windowed controls are disabled.
The separate original utilities and source/license remain bundled in the manual
package and install-missing AmiPkg installer.

Control follows the bundled upstream ZZScanlines code: discover the Zorro board
at runtime, write 16-bit parity 0 at offset 0x100e, then mode at 0x100c. No ARM
pixel dimming, per-frame utility execution, firmware flash or startup changes.
The registers are write-only/global. Normal cleanup disables the effect before
closing the private screen; it cannot restore an unreadable prior setting.
Windowed runs do not write these controls. A forced reset cannot promise cleanup.

Legacy software preferences map Soft→Soft, Smooth→Gradient, Hard→Classic on
load. Saving writes a distinct zzscanlines key; existing config files are not
changed automatically. Direct rendering, COPY and test captures retain full
brightness. FPGA scanlines occur after the framebuffer and are absent from
normal screenshots. The user confirmed the effect on the physical display.

## Frontier: Elite II intro

A500/Kickstart1.3, 512 KiB Chip +512 KiB Slow, compatible 68000 interpreter,
PAL fullscreen, 30 FPS presentation limit, AHI 32 kHz stereo, disk1 read-only.
Both samples use completed presentation counters 3,750→4,500, after the intro
was observed. No screenshot/transfer occurred inside these intervals.

| Scanlines | Displayed frames | Interval | Average displayed FPS |
|---|---:|---:|---:|
| Previous software Soft | 750 | 38.005 s | 19.73 |
| Xanxi FPGA Soft | 750 | 33.492 s | 22.39 |

The observed difference is +13.47%. This is one indicative pair, not a matched
unique-game-frame benchmark. The scenes are not synchronized by guest frame,
and the FPGA run recorded 88 input events versus zero in the first run. Do not
interpret this as a measured guest CPU or Frontier 3D-engine speedup. The user
also reported visually smoother/faster motion. Both runs exited cleanly with
zero register/cache witness mismatches; preferences remained unchanged.

## Test-only presentation

Normal play now omits both the FPS overlay and decorative edge/rainbow border.
`ZZUAE -test` (or icon TEST=YES) exposes the FPS control in Testing; bounded
fullscreen tests retain the diagnostic border. F9 firmware scanlines remains
available in normal fullscreen play. SHOWFPS without a bounded test run is
rejected by the CLI, rather than silently enabling a normal-play overlay.
The Frontier comparison above was recorded before this UI-only restriction.

## Verification

Native tests cover mode cycling, untouched windowed state, exit disable,
legacy preference migration/round trip and test-only FPS command generation.
ARM instruction-model checks cover all pixel formats/sizes, full-brightness
output even with the old shared scanline word set, source capture, bounds,
cancellation, mapping removal and preservation of D0–D31/FPSCR. Both direct and
COPY paths pass. Framework tests pass. Physical F9 cycling through all four
modes and F10 cleanup passed in an additional session.
