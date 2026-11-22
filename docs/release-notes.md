# ZZUAE 0.6.1 Beta

Application/launcher version: **0.6.1-dev**. AmiPkg version: **0.6.1-dev**.

## Changes

- Rebuild the launcher with the next numbered release; remove the dated package suffix.
- Include Settings → ZZOverclock, with 666.7 MHz and experimental 800 MHz controls.
- Retain the recorded emulator players and their build identifiers. This release does not rebuild or relabel those cores.
- Update the main README and linked feature documentation.

Includes the current launcher and players: A1200/AGA profile, A600 HDF/USB support, picture positioning, splash fixes, Amiga+Esc menu and 22/27/original-rate PCM choices. Interpreter remains the default. Optional FPU/Cyclone players retain their stock-clock gates; they are not validated at 800 MHz.

## Installation and compatibility

Extract the LHA, open its drawer and double-click Install. Choose a writable
destination and close emulators before updating. Dependency checks and existing
settings/saves are preserved. Clock control requires the optional ABI 3 firmware
service; its absence disables clock controls only. The clock affects the whole
board. No firmware is installed and no clock change happens automatically.
Use suitable cooling for 800 MHz; temperature preflight is not a continuous
thermal watchdog. No new performance gain is claimed here.

## Verification

All launchers were cross-compiled into separate release directories. Recorded
player hashes are retained. Installer signatures, payload hashes, extraction,
component references and application version strings are checked before publication.
Prior hardware evidence remains separate from these package checks.
