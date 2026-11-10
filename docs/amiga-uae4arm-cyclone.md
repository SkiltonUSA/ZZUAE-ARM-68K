# ZZUAE-Cyclone Experimental Core

Choose **CPU → ZZUAE-Cyclone Experimental Core** in ZZUAE. The launcher runs
`ZZUAE-Cyclone` from the application drawer. **68000 compatible** remains the
default; saved settings keep their existing engine selection. Save remembers a
new selection. If the optional player is missing, the launcher reports its name.

Cyclone is an ARM assembly **68000 interpreter**, not a JIT. It uses 32 MiB of
Exec-owned ZZ9000 RAM and shares ZZUAE's OCS/ECS chipset, display, mouse,
joystick, Paula/AHI, second floppy and RTC support. The FPU selector is disabled
for Cyclone. No 68020 or 68882 instructions are provided, and instruction
prefetch is not emulated. Software that depends on exact CPU timing may behave
differently. Return to **68000 compatible** if a game misbehaves.

The earlier physical evaluation found mixed results: Workbench boot took 2.6%
longer; single-pair Frontier, Badlands and State of the Art workloads took 4.9%,
0.9% and 1.1% less elapsed time. These are whole-emulator test times, not game
FPS or a general speed guarantee. The integration checks below do not turn
those earlier measurements into a claim about every game.

## Implementation

Pinned [Cyclone68000](https://github.com/notaz/cyclone68000) revision
`fe89d4e2fb7b876ec71d7a8ce66affbbdf91104d`, GPLv2 licensing option.
Credit: FinalDave and Gražvydas “notaz” Ignotas.

- The generator emits Cortex-A9-compatible ARM32 instructions. Instruction
  fetches use `REV16`/`REVSH` and adjusted immediate-byte addressing to read
  UAE's big-endian memory directly. Data accesses use UAE memory handlers.
- The adapter advances chipset time after each guest instruction. It exchanges
  CPU context at batch, interrupt, STOP and fault boundaries. It retains normal
  Core1 cancellation and mandatory MMU/cache/register teardown.
- MOVEM odd-address exceptions restore the saved guest instruction pointer
  before entering Cyclone's exception handler. Upstream reused ARM register r4
  as a context pointer, which could otherwise contaminate the stacked guest PC.
  A generated-code regression checks word/long reads and writes at different
  host context addresses, plus aligned transfers.

## Build and checks

After preparing the usual ZZUAE toolchain, mapping probe and libc/libgcc:

```sh
python3 scripts/build_uae4arm_cyclone.py
python3 scripts/build_uae4arm_launcher.py
```

The optional player and manifest are under
`.context/amiga/uae4arm/cyclone-events/`; the player is
`machine/ZZUAE-Cyclone`. Normal engine outputs are separate.
`--conservative` and `--direct` are comparison builds, not launcher choices.
Release packaging accepts `--cyclone-player` and `--cyclone-manifest` together;
it checks the recorded version/hash and includes the license and this guide.
All required core objects are rebuilt or source/flag-hash checked within that
variant; objects are not borrowed from an older experimental build.

The build audits unsupported ARM instructions and records the same product
version as the launcher. The generated assembly and source hashes are retained
with the build. For the MOVEM regression:

```sh
python3 scripts/build_uae4arm_cyclone_probe.py --big-endian --fix-movem
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/cyclone_movem.py
```

Launcher tests cover engine routing, settings round-tripping, existing engine
indices and rejecting a Cyclone/FPU combination. ARM model checks establish
instruction-level behaviour only; they do not prove physical audio quality or
cycle-exact chipset compatibility.

## Integration verification

Launcher settings/command tests, strict 68k builds, the MOVEM ARM regression,
A500/A600 synthetic chipset/audio/input/DF1/RTC checks and worker lifecycle tests
passed. Cancellation includes unlimited-play cancellation. The optional ZIP
packaging check verified executable hashes, license inclusion and exclusion of
ROMs, disks and preferences.

Physical A4000TX checks completed before the final display-name-only rebuild:

| Run | Guest frames | Displayed frames | Sound | Queue gaps |
|---|---:|---:|---|---:|
| Workbench 1.3, window, DF1 + RTC | 500 | 500 | Off | — |
| Frontier, window, DF1 + RTC | 1,800 | 1,078 | Paula | 2 |
| Badlands, fullscreen + RTC | 1,800 | 1,065 | Paula | 2 |
| A600 / Workbench 2.0, window + RTC | 800 | 478 | AHI | 2 |

All four returned successfully with zero register/cache-witness mismatches and
released their owned allocation. Badlands reached its title and generated
nonzero PCM. The short Frontier check was still at its startup Shell; it does
not establish gameplay or music compatibility. Workbench/AHI produced silence,
so that run verifies transport and cleanup, not audible quality. No listening
confirmation or new performance gain is claimed. Rendering at 30 FPS deliberately
presents fewer frames than the guest executes.

The final launcher/player use **ZZUAE-Cyclone Experimental Core** as the display
name and share version 0.5.7-dev. After reconnecting, the final named build passed
an actual MUI-launcher Badlands test: 1,800 guest frames, 1,080 drawn and 880
completed host presentations. Paula submitted/completed 998,400 sample frames,
with two queue gaps and no driver error. Register/cache-witness restoration and
owned-memory release passed. This was a lifecycle check with screenshot traffic,
not a matched performance benchmark or listening test.

The CPU selection and disabled FPU control were verified visually. The initial
testing window was blank until resized; normal reopening then drew correctly.
This redraw issue remains to reproduce.
The launcher and optional player are installed in `SD032G:Emulator/ZZUAE`.
The prior launcher is in `Rollback-Cyclone-057`; saved settings and existing
players were checksum-verified unchanged. Local evidence is in
`.context/cyclone-integration/`. No GitHub release has been
published for this optional integration.
