# ZZUAE remaining work

Current release: **0.6.3 Beta**. [Release notes](release-notes.md).

## Active work

- Broaden experimental JIT, self-modifying-code, Cyclone and FPU compatibility,
  sustained gameplay and input coverage. The interpreter remains the default;
  the tested A1200 JIT was slower. The latest 6,000-frame Banshee interpreter/JIT
  runs reach gameplay with identical final guest pixels and clean exits, but
  retain audio gaps. [Results](validation/session-storage/README.md).
  A new Cyclone candidate passes a writable disk-swap run at 800 MHz; the
  published Cyclone binary retains its stock-clock restriction.
- Continue general audio continuity and Paula/AHI listening checks. Heavy scenes
  may miss audio deadlines; clean exit or sample accounting is not listening approval.
- Finish broader multi-disk-game checks and promote paired session-menu players.
  Compatible, FPU and Cyclone candidates pass guest writes, swaps, reinsertion
  and filesystem checks. Public 0.6.3 does not contain them.
- Complete wider PCMCIA CF image/guest-driver validation and package the paired
  launcher/player. The experimental adapter passes native, ARM and physical
  A600/A1200 FAT file read/write checks. [Evidence and setup](validation/storage-compatibility/README.md).
- Extend physical USB SD access beyond the compatible A600 path to A1200.
  Poseidon currently enumerates no card reader despite the card being connected;
  all unit opens fail before guest startup. Hardware check pending.
- Broaden A600 game/peripheral and physical USB joystick validation.
- Guest FPU remains double-backed, not full 68882 extended precision.

## Completed

- FPU-player clock scaling and bounded PAL/NTSC boot, Banshee gameplay, delivery
  and teardown checks. [Evidence](validation/fpu-clock/README.md).
- Sound-off display caps no longer slow guest time in normal, accelerated and
  FPU players. [0.6.3 validation](validation/cadence-integration/README.md).
- Signed 0.6.3 AmiPkg and matching build identities. These are not pending tasks.

## Parked

Acid in the House and State of the Art investigations; Core0 Copper/AGA and
RasterIX offloading experiments that did not establish a useful end-to-end gain.
Historical measurements remain labelled with their tested builds.
