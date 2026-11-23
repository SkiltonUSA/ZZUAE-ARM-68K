# Wider sprite-span comparison

The private sprite recorder remains **unpromoted**. Its repeated 0.57–0.63%
Banshee gain did not carry over to Slam Tilt. The installed normal/FPU players
and interpreter default remain unchanged.

## Matched physical tests

Both players used A1200/68020 interpreter mode, PAL, the same disk and scripted
inputs, fullscreen output and Paula audio. The first pair stopped in the intro.
A second pair used identical extended test harnesses with additional inputs and
9,000 guest frames; both reached the pinball table. Only the candidate's sprite
recording implementation differs between each pair.

| Workload | Guest frames | Reference emulated FPS | Candidate emulated FPS | Change |
|---|---:|---:|---:|---:|
| Slam Tilt intro | 6,000 | 48.997 | 48.909 | −0.18% |
| Slam Tilt boot through table | 9,000 | 46.679 | 46.526 | −0.33% |

These small differences are single paired observations, not a demonstrated
regression. The intro is close to the pacing ceiling. Neither number measures
sustained active pinball gameplay or the table alone. Together with Banshee,
the results do not establish a useful general performance gain.

All four runs completed their requested guest frames with matching final guest
dispatch/cycle counts, PC and framebuffer within each pair. Both extended builds
also passed the four ARM instruction-model fixtures before hardware testing.

For the extended pair, both runs completed 4,995,072 PCM sample frames at a
27,710 Hz source rate, with device error zero. Late-submit gaps were 1,263 for
the reference and 1,323 for the candidate. This is not an audible-quality test
or an audio fix. Registers, MMU/cache witnesses and owned-memory release passed
on every run; transport reported no failure.

![Slam Tilt table reached by both extended runs](sprite-wider/table-reference/final.png)

This is the raw emulator framebuffer capture, not a Workbench display capture.
The final image hash matches between reference and candidate.

## Frame-counter interpretation

Whole-run emulated FPS divides completed guest frames by `BOOT elapsed_us`.
The host's `PROGRESS frames` counter instead counts **displayed** frames. Audio
pacing can skip presentation, so its interval rates must not be called emulated
FPS. The extended reference presented 4,444 of 9,000 guest frames; the candidate
presented 4,374. A late interval near 10 displayed FPS does not establish a
10 FPS emulation rate for that interval.

The private runner now names this field `last_intervals_displayed_fps`.
Legacy summaries only equate interval display and emulation rates when the log
confirms every guest frame was presented. Archived metrics here use the explicit
name; the raw console logs retain their original output. Whole-run measurements
are unaffected. Earlier sound-off Banshee runs that presented every frame are
also unaffected.

## Outcome and next work

Keep the existing pixel-loop build. The sprite candidate and its native/ARM
equivalence tests remain available for future workloads, but are not a new
default or release. This follow-up adds four physical runs / 30,000 guest frames.
Private test players were removed and installed normal/FPU hashes rechecked.

The next useful measurement is a narrowly sampled breakdown inside sprite
decision/event handling, separating visible recording from decisions that
produce no visible span. Any proposed shortcut must preserve mid-line register
writes, DMA, clipping and collision behaviour. The current recorder substitution
does not address enough of that cost to solve the PCM production deficit.

Evidence: [scripts, build hashes and run logs](sprite-wider/).
Earlier candidate details: [sound-enabled profiling](REMAINING-COSTS.md).
