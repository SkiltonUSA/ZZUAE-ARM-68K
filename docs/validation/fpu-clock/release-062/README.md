# 0.6.2 Beta installer validation

A fresh installation into an isolated Amiga drawer passed dependencies and
signature checks. Reinstalling the same package preserved an unrelated settings
sentinel. The installed launcher and FPU player matched the packaged hashes.

The installed FPU player completed a 120-frame A600 Workbench 2.0 boot using
68882, interpreter, PAL and Paula 22 kHz at the retained 800 MHz board clock.
Timer calibration reported 400 ticks/us. VFP state, register restoration and
cache witness checks passed, and owned memory was released. Core1 was idle and
Core0 AGA inactive afterwards. This boot is silent and does not assess music quality.

[Fresh install](install.txt), [upgrade](upgrade.txt), [boot and teardown](player.txt).
The final archive includes a documentation-only README correction after these
checks; the application and player binaries are unchanged.

The final published archive was subsequently installed into the existing
SD032G:Emulator/ZZUAE drawer. Installed normal/JIT/Cyclone player hashes matched
the retained package binaries before updating. Launcher/FPU backups were kept
in SD032G:Dev/UAE062Final; the new installed hashes matched the package.
Dependencies and installation passed, Core1 was idle afterwards and the board
remained at 800 MHz. [Production installation](production-install.txt).
