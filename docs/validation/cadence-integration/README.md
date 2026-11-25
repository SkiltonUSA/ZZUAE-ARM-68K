# Cadence integration — 0.6.3

Normal 68000, non-FPU 68020/JIT and optional FPU players now apply the validated
sound-off display cadence. Reduced display rates skip drawing, not guest frames.
PAL/NTSC CPU/chipset time continues independently; MAX stays uncapped with sound off.
Sound-on decisions and synthesis are unchanged.

The retained normal and accelerated objects reproduce their recorded ELF payloads
exactly, and those complete ARM images are found in the 0.6.2 release executables.
Only the live display adapter is rebuilt. FPU uses its recorded CPU/chipset build.
The final 0.6.3 builds have identical ARM images and generated host sources to the
hardware-tested candidates; the application version string changes.
[Build identities](builds.json).

All 17 bounded physical runs pass: reference/candidate PAL25 sound-off, PAL30
Paula and candidate NTSC30 fullscreen for all three players, plus an actual
JIT-engine reference/candidate pair. Each paired run matches guest cycles, PC
and diagnostic hash. These are checksums, not full machine-state comparisons.
Sound-on pairs complete all queued samples with zero device errors and one
recorded queue gap each. They do not prove listening quality.
[Measurements](hardware.json).

Six 1,800-frame real-disk runs exercise Alien Syndrome, Banshee demo and Frontier
in windows and fullscreen, with bare Esc, Amiga+Esc pause/resume and guest keyboard
input. All restore registers/cache witnesses, complete audio and release memory.
These are bounded disk-boot and input/lifecycle checks, not complete gameplay
or audible-quality acceptance. Writes are temporary; no original disk is changed.
[Results](games/summary.json).

Native sanitizer checks cover cadence, host setup/rate choices, runtime clocks,
picture positioning, RGB565 mappings and session-menu gates. Tests run at the
existing 800 MHz KEEP setting; no firmware/clock change is made. Final Core1 is
idle and Core0 has no active work. Cyclone is retained separately, not tested here.

The former PAL25 sound-off slow motion is corrected; this is not a JIT or CPU
throughput gain. Heavy-game audio and compatibility limitations remain.
