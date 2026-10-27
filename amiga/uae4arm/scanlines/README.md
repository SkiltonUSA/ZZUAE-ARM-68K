# Bundled ZZScanlines

Original utility by [Xanxi](https://github.com/Xanxi-Amiga/zz9000-scanlines),
pinned in `upstream.json`; source and GPL-3.0-or-later license are in `vendor/`.

The ZZUAE launcher’s Firmware / ZZScanlines button prefers an existing utility
in `SYS:Utilities/ZZScanlines` or `C:` and otherwise opens its bundled copy in
`PROGDIR:Scanlines`. Opening the utility does not change the scanline mode;
choose a setting and Apply in its window.

Compatible FPGA firmware and a supported low-resolution, non-interlaced display
mode are required. High-resolution RTG Workbench is normally unaffected. The
current windowed ZZUAE prototype does not automatically switch Workbench modes.
This utility controls the whole display, not an individual emulation window.
No firmware is flashed and no startup files are changed.

`Install-Scanlines` installs missing tools into `SYS:Utilities/ZZScanlines` while
preserving existing utilities, including ones already in `C:`. The bundled
copies also work without installing system-wide.

ZZUAE now uses this FPGA interface exclusively. The fullscreen selector and F9
use Off / Classic / Soft / Gradient, with parity 0. Control is integrated into
the player using the runtime-discovered board address and the upstream 16-bit
register writes at offsets 0x100c/0x100e. It does not spawn a utility per frame.
The controls are write-only: the player disables scanlines on exit rather than
claiming to restore an unreadable earlier value. Windowed runs do not touch them.
Software dimming has been removed from direct display, COPY and test capture.

Framebuffer screenshots cannot show the effect applied later in the FPGA.
A physical display check is required to confirm the appearance.
