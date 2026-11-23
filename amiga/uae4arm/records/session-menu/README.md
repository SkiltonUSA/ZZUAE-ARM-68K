# Amiga+Esc session menu verification

The native host menu preserves guest Esc input and existing ARM payloads.
See [controls and implementation](../../../../docs/amiga-uae4arm-session-menu.md).

Sanitizer checks pass Escape modifier/release ordering, frame-checkpoint gating,
bounded audio drain and ring wrap/full/empty handling. Shared ZZ8-Bit host
compilation still passes with this extension disabled.

Physical tests pass normal-player window/fullscreen and 68020-interpreter
fullscreen menu interaction with Paula: both Amiga keys, resume, scanline cycle,
exit confirmation, zero input overflow and clean state/memory restoration.
The final fullscreen tests each presented 484 frames. Audio queued/submitted/
completed totals agree and workers report error=0. Intentional pauses count
as delivery gaps; these checks do not establish audible quality or a speed gain.
The optional FPU/Cyclone hosts are compiled only at this stage because their
existing clock gates exclude the retained 800 MHz configuration.

An initial probe sent input before the player window existed; the harness now
waits for the window. A repeated fullscreen test exposed missing menu focus;
explicit WindowToFront/ActivateWindow passed subsequent checks, including capture
of the screen while paused. Settings and firmware were not changed.
