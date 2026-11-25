# 0.6.3 installer acceptance

The signed AmiPkg passes fresh and repeat installations and updates the main
ZZUAE drawer. All four executable hashes and installed README/credits/licence
hashes match the local package. Dependency checks and catalogue signatures pass.
The existing configuration and retained Cyclone binary are unchanged. An untracked
preservation-test file survives repeat installation.

The installed normal, accelerated and FPU players each run 120 PAL guest frames
with sound off and a 25 FPS display cap: 60 frames drawn, 60 skipped, full guest
progress, clean register/cache restoration and allocation release. Final Core1
is idle; Core0 has no active work; 800 MHz KEEP remains held without a clock fault.
No firmware or startup file is changed. Existing ZZScanlines tools are preserved.

The package checker also rejects the stale 0.5.7 installed ReadMe.txt found in
the previous archive. The replacement is an exact copy of the main README.
The existing archive-level README, credits and full licence requirements remain.
