# Window status lights

Two 6×6 lamps sit in a separate 12-pixel strip below the guest picture. Green
means a frame has been displayed and execution has not been stopped. Red uses
the core's DF0 GUI indicator (selected/motor activity, including writing).

The ARM publishes the DF0 state in its own shared status cache line. The host
invalidates that word before reading it and repaints only on a state change or
window refresh, after any direct bitmap lock has been released. Fullscreen and
the guest rendering dimensions remain unchanged. Mouse capture excludes the strip.

The new instruction-model test failed on the previous binary, then passed on
compatible, JIT and optional-FPU builds: disk on, write state, disk off and
unrelated GUI LED isolation. Existing mouse, keyboard, RAM/profile and optional
FPU arithmetic/restoration checks also passed. Cross-builds passed with warnings
as errors. ZIP and signed offline AmiPkg builds were refreshed locally.

Three players were transferred and CRC-verified in temporary storage on the
Amiga. Physical LED observation and installation are pending: the A600 session
was still running, and was preserved. No installed binary, preference or saved
configuration changed in this turn. The public release remains unchanged.
