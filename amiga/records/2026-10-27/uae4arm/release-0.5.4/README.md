# ZZUAE 0.5.4 Beta package checks

Runtime version: 0.5.4-dev. ZIP and offline AmiPkg LHA include the compatible,
JIT and optional FPU players. The launcher and all three players match the
CRC-verified executables installed and tested on the A4000TX.

Passed: ZIP/LHA payload equivalence, executable sizes/hashes, all member hashes,
C and Python signature verification, corruption rejection, dependency-first
installation order, icon types and private-media exclusions. Source is supplied
separately with the pinned UAE4ARM and picolibc sources.

The refreshed installer archive was not reinstalled on hardware. Prior hardware
results remain in ../window-leds; experimental CPU/audio limitations remain.
