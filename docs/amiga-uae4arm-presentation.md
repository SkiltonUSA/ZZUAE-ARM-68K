# ZZUAE FPS counter and native PAL fullscreen

Development 0.5.4-dev adds a saved FPS On/Off choice beside Frame rate in the
launcher. The top overlay reads `ZZ9000 n.n FPS`. It counts completed presented
frames over intervals of at least one second, using the host timer. It is not
the configured cap, guest PAL frame count or a CPU-speed measurement. Refresh
redraws do not increment it. It counts completed blits, not HDMI refreshes,
and does not establish tear-free scanout. No new firmware service is required.

The Output choices are Window and Fullscreen PAL. Window keeps the existing
square-pixel 4:3 fit, up to 640×480. Fullscreen opens a separate **320×256,
32-bit PAL RTG screen**, as requested. It uses the full guest raster, with a
one-pixel decorative outline and rainbow accent over the outer edge. This
avoids shrinking a low-resolution game to make room for a large bezel. The FPS
label is an optional overlay over the upper left of the picture.

Native PAL pixels are not square: the monitor should present this signal at
4:3, rather than stretch it over a widescreen panel. Workbench ScreenMode
preferences are never changed or saved. An exact installed 320×256 32-bit RTG
mode is required; unsupported machines get a startup error rather than a
silent substitution. The tested A4000TX provides mode `50011303`.

Existing configurations remain readable. `fullscreen=0/1` selects Window or
Fullscreen PAL; `showfps=0/1` controls the overlay. The player accepts
`FULLSCREEN` and `SHOWFPS` only with live display. The launcher omits those
switches for capture-only testing. Switching modes during play is not added.
F9 still cycles **software** scanlines; F10 exits. Xanxi's bundled **ZZScanlines**
firmware utility remains a separate control, not automatically enabled by F9.
Avoid enabling both scanline implementations together.

## Implementation

ARM renders only the OS-allocated, locked offscreen bitmap. The established
nonce challenge, temporary NC/XN mapping, ACK, unlock and WaitBlit ownership
sequence remains. The common RTG aperture and mapping limits were not changed.
Native PAL adds a 320×256 output shape; horizontal downsampling maps the existing
640×256 source to 320×256, retaining every source row. Existing NEON conversion
continues on the 640-pixel window path; PAL uses the smaller scalar conversion.

The 68K paints the small edge decoration and FPS label after presentation. The
private fullscreen screen owns its palette. Window mode obtains/releases its
text pens without changing the desktop palette. Normal and experimental JIT
players share the same display implementation. No CPU-engine or emulated
chipset timing change is part of this work.

## Hardware measurement

State of the Art, A500/Kickstart 1.3, 512 KiB Chip + 512 KiB Slow RAM, AHI
32 kHz stereo, Soft software scanlines and 30 FPS cap: **1,193 displayed frames
in 61.789 seconds = 19.31 FPS** at native PAL 320×256. The run completed all
3,000 guest frames with 29,718,700 instructions, 372,192,964 cycles and final
RGB565 CRC `4B424AAC`, matching the earlier renderer checks. Cache/MMU/register
restoration and owned-memory release passed. The smaller screen substantially
reduces host blit time, but this single run does not establish an overall FPS
gain. Audio queue gaps remain; listening quality was not assessed.

## Verification

- Native ASan/UBSan: settings round-trip/command generation, native PAL and
  4:3 window sizes, measured FPS across timer wrap and long stalls.
- Cortex-A9 instruction model: PAL plus three window sizes, both supported
  32-bit formats, scanline modes, row guards, snapshots, invalid geometry,
  ownership rejection, cancellation/unmapping and D0–D31/FPSCR preservation.
- JIT worker model: success, cancellation, invalid options and unlimited-run stop.
- Physical JIT player: 180-frame PAL startup, FPS overlay, 3,012 translated sites
  and 16 fallback sites; clean restoration and release. This is a startup check,
  not a new JIT game-compatibility or performance claim.
- Framework: `make test-amiga-arm test-amiga` passed. Protocol tests remain
  separate from physical hardware evidence.

The public release download remains 0.5.3; these changes are development source.
Detailed local test records are in `.context/amiga/uae4arm/presentation/`.

Installed matching launcher and both players on the A4000TX. Native fullscreen
normal play passed F9/F10 and cleanup after the title-strip correction. The
launcher reopens with the FPS option visible. Saved application and Workbench
screen-mode preferences were unchanged; prior files remain available for rollback.
[Selected test records](../amiga/records/2026-10-27/uae4arm/presentation/).

## Work log

Added failing configuration/geometry tests and the pure FPS helper; integrated
settings and display. Cross-compiled the launcher and both players. Hardware
screenshots exposed approximated colours, corrected by assigning the private
screen palette explicitly. A larger desktop-resolution bezel was tested, then
replaced with native PAL 320×256 following the requested resolution change.
Its row-expansion code and Large setting were removed. External emulator reviews
were recorded separately; no code from those repositories was imported.

Current development update: FPS controls and the decorative border are test-only
(`ZZUAE -test`). Normal play shows neither. See [ZZScanlines and Frontier results](amiga-uae4arm-zzscanlines.md).
