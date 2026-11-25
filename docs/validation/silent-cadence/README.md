# Sound-off presentation cadence experiment

The released 0.6.2 player ties sound-off guest progress to every displayed frame.
Selecting 25 FPS therefore slows PAL guest execution to about half speed. This
candidate applies the existing frame-selection accumulator with sound off as
well as on: CPU, chipset, Copper and Paula advance on every emulated frame;
drawing and host publication occur only at the requested display cadence.
The host paces those publications. MAX remains uncapped with sound off.
A requested display rate above the PAL/NTSC guest rate is clamped to that rate.

This is an isolated FPU-player experiment, **not an installed release change**.
It uses the interpreter; no JIT, FPU arithmetic, clock or firmware change is
responsible for the result. Sound-on pacing and pressure decisions are retained.
A skipped draw still polls guest input; interactive input/pause acceptance is
not established by the no-input fixture below.
The test-only final-frame drawing override is also retained.

## Validation

[Matched hardware measurements](hardware.json) and [build identities](builds.json)
record the reference and candidate separately. Both recompile the same live
adapter against the recorded CPU/chipset objects; only the candidate enables
`ZZUAE_SILENT_CADENCE` and its matching host display-rate plan. Neither binary is
claimed to be byte-identical to the installed player. The two builds use the
same 32 MiB executable cache and 72 MiB runtime allocation.

Tests use the [original synthetic Paula-tone ROM](../../../tests/amiga/uae4arm/make_audio_rom.py)
and a zero-filled 901,120-byte read-only ADF, with
600 guest frames, interpreter020, optional 68882 enabled, and the existing
800 MHz setting. Guest cycle count, final PC and diagnostic hash are compared
between each reference/candidate pair. They are not a complete machine-state
serialization or a gameplay compatibility test. The fixture executes no guest
FPU arithmetic. Reported elapsed time is the player's bounded boot/run interval;
it is not a game-rendering FPS benchmark.

All 16 matched hardware runs pass, with identical guest cycle count, final PC
and diagnostic hash in each pair. Each restores ARM registers/cache witnesses
and releases its allocation. Sound-on runs complete every queued audio sample
without a device error. Both builds report one queue-gap event in each sound-on
run; this is not a listening result or a fix for heavy-game audio starvation.

| Mode | Display cap | Sound | Reference seconds | Candidate seconds | Reference / candidate draws |
|---|---:|---|---:|---:|---:|
| PAL | 25 | OFF | 24.815 | 12.537 | 600 / 300 |
| PAL | 30 | OFF | 20.884 | 12.571 | 600 / 360 |
| NTSC | 25 | OFF | 24.791 | 10.495 | 600 / 250 |
| NTSC | 30 | OFF | 20.841 | 10.516 | 600 / 300 |
| PAL | 50 | OFF | 12.872 | 12.821 | 600 / 600 |
| NTSC | 60 | OFF | 10.862 | 10.827 | 600 / 600 |
| PAL | 25 | PAULA | 11.796 | 11.791 | 298 / 298 |
| NTSC | 30 | PAULA | 9.847 | 9.778 | 297 / 297 |

The reduced-cap results correct guest slowdown; they are not a claimed CPU/JIT
speedup. Full-rate sound-off and sound-on controls remain close to the reference.
The nominal PAL/NTSC totals are 12/10 seconds for 600 frames; reported intervals
include run startup/transport overhead and, with sound, buffered completion.

Six additional [display/rate boundary runs](extended.json) pass: PAL 25 and NTSC
30 fullscreen; PAL requested 60 (clamped to 50); NTSC requested 50 (500 draws
from 600 guest frames); and uncapped MAX on both. Their guest cycle/PC/hash
values match the corresponding reference modes. Fullscreen checks cover this
synthetic fixture, not arbitrary game modes or visual acceptance. Final status
shows Core1 idle, no active AGA work, clock KEEP retained and no clock fault.
The bridge reservation was released; no emulator was left running.

Native AddressSanitizer/UndefinedBehaviorSanitizer checks cover PAL/NTSC at
25/30/50/60/MAX, sound on/off, frame-count/time preservation, rate clamping,
clock rollover and timeout behavior. The alternate late-publication compile
path builds, but is not the path used by these hardware runs. The RGB565 mapping
regression covers pitch, aperture limits, cross-section page mappings, occupied
mapping refusal and unmapping. This restores a missing standalone header
definition already referenced by the renderer, not a newly enabled video mode.

## Reproduce

Use the prepared workspace described in [the build guide](../../build.md):

```sh
python3 scripts/build_fpu_clock.py --workspace /path/to/prepared/workspace \
  --base /path/to/recorded/fpu-execution --output /path/to/reference \
  --silent-reference
python3 scripts/build_fpu_clock.py --workspace /path/to/prepared/workspace \
  --base /path/to/recorded/fpu-execution --output /path/to/candidate \
  --silent-cadence
```

Run the focused native tests from this repository:

```sh
clang++ -std=c++11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  tests/amiga/uae4arm/silent_cadence.cpp -o /tmp/zzuae-cadence
/tmp/zzuae-cadence
clang -std=c99 -Wall -Wextra -Werror -fsanitize=address,undefined \
  tests/amiga/uae4arm/rtg565.c -o /tmp/zzuae-rtg565
/tmp/zzuae-rtg565
```

The recorded base and output paths must be separate. The standard build without
these switches keeps existing behavior. The switches cannot be combined.
[Native checks](native.txt) and the hardware logs accompany this record.

## Promotion limits

Normal compatible-68000 and non-FPU player builds still need the same integration
and testing. Real-game behavior, input during skipped frames, pause/resume,
real-game fullscreen and subjective audio acceptance need their own checks before
promotion. No package, saved setting or production executable is changed by
this experiment. Sound-off MAX intentionally has no real-time cap.
