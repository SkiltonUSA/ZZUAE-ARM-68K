# Session menu

Press either **Amiga key + Esc** to pause and open the session menu in a window
or fullscreen. Plain Esc and Shift+Esc reach the emulated Amiga.

- **Resume** returns to the game. Esc also resumes from the menu.
- **Scanlines** cycles the existing firmware modes in low-resolution fullscreen.
- **Screenshot** appears only in testing mode.
- **Exit emulator** asks for confirmation. Amiga+F10 remains the direct exit shortcut.

Opening the menu releases window mouse capture. After Resume, click the game
picture to capture again. Arrow keys and Return, or the mouse, select menu items.
Disk insertion and save-state controls are not part of this menu.

## Implementation

The native host waits for a published frame with no bitmap lock or conversion
grant outstanding, then withholds the normal grant/acknowledgement. Core1 remains
at its existing frame handshake, servicing input reset and cancellation. The
host drains queued audio through the existing worker; it does not close/reopen
the audio device or reset producer indices. Drain failure takes the normal
cooperative stop path. Resume clears held input and excludes pause time from
pacing/FPS measurements and the bounded-test watchdog.

`ZZUAE_SESSION_MENU` enables this host-only extension. The shared host template
still builds ZZ8-Bit with its own menu. ARM payloads and guest timing are unchanged.

## Verification

Native sanitizer tests cover Escape down/up pairing, the unlocked-frame gate,
audio drain completion/failure/timeout, and the existing audio-ring transfer cases.
Physical Paula tests cover window/fullscreen menu opening with either Amiga key,
plain/shifted Esc passing the host shortcut filter, mouse release, repeated resume,
firmware scanline cycling and exit confirmation. These are transport/lifecycle
checks, not a new audible-quality or performance claim.

The FPU player supports calibrated stock/800 MHz timing since 0.6.2. Its menu
now also passes the 0.6.3 cadence checks at 800 MHz. The optional Cyclone player
retains its stock-clock restriction.
