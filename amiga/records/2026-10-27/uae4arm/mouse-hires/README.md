# Mouse and HiRes validation

- Reproduced missing guest mouse-counter updates; restored guest input-frame timing.
- Added 640×512 fullscreen output and verified real ARM conversion/bounds/mapping and SIMD preservation.
- Checked compatible fullscreen and window SysInfo; the user confirmed input, then requested easier window control.
- Added native click capture with F8 release; raw events stay in a bounded host queue until the ARM input mailbox has room.
- Physically checked capture, guest Memory-button click, F8 release, recapture, focus loss and F10 exit; no capture/input queue overflow, handler removed, complete restoration and owned-memory release.
- CRC-verified installation of launcher plus compatible/JIT/FPU players, with rollback copies. Saved emulator and Workbench screen settings were preserved.
- Rebuilt ZIP and signed offline AmiPkg installer locally; public release unchanged.

JIT/FPU mouse and FPU lifecycle checks are instruction-model results. Physical capture acceptance used the compatible player; no whole-emulator performance improvement is claimed.

UB companion tools cover Python only: no new duplicate candidates; existing build/audit complexity remains. Mutation sites were scanned, not executed; no new mutation-coverage claim. C input handling is covered by sanitizer-backed queue tests and physical interaction/cleanup checks.
