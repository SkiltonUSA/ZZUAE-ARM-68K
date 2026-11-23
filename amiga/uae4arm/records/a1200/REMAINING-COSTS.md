# A1200 remaining costs: sound-enabled profiling

Private follow-up to [idle-fetch and AX tests](IDLE-FETCH.md), using the current
pixel4 interpreter base, PAL A1200, Banshee's playable demo, native fullscreen,
Paula 27,710 Hz and the same deterministic guest inputs. Every physical run is
bounded to 6,000 guest frames. Instrumented frame rates are not speed claims.

## CPU dispatch profile

Sampling begins at guest frame 3,000; approximately one in 256 dispatches is
timed. 302,101 samples were collected from 76,945,079 dispatches in that section.
The first five intervals do not overlap:

| Stage | Sampled dispatch time |
|---|---:|
| Advance chipset events | 57.11% |
| Execute 68020 opcode, including memory/device accesses | 21.91% |
| Special service: interrupts, Copper and CPU flags | 15.62% |
| Dispatch bookkeeping | 5.36% |
| JIT validation | 0% |

Explicit Copper service is 2.08% **within** special service; STOP waiting is
zero in these samples. Event time includes callbacks and waits, not scheduler
bookkeeping alone. Timer reads, instrumentation and layout affect the result.
This is not an exact whole-run wall-clock breakdown. The result confirms that
chipset/event work remains the larger target with audio enabled.

The profile passed the four actual ARM memory, IRQ, beam and colour fixtures.
The physical run completed in 171.600 seconds, with matching reference dispatch
count, cycles, final PC and framebuffer. All 3,330,048 queued sample frames
completed with device error zero and clean Core1 restoration/release.

## Disabled collision planes

`do_sprite_collisions` originally loads a private `line_data` word and extracts
its bit before testing whether that plane participates in collision matching.
The candidate skips a disabled plane before that load. It leaves enabled-plane
matching, dual-playfield behaviour, sprite grouping, latched collision bits and
all guest DMA/CPU/Copper timing unchanged. The memory being avoided is private
collision data, not guest-visible device reads or Zorro transfers.

A sanitized native test extracts the original function and compares its final
collision register against the candidate over 200,000 randomized cases. It
covers both OCS/ECS and AGA plane limits, single/dual playfields, all 256 enable
masks, random match masks and existing collision bits, zero to eight recorded
planes, sprite masks, ranges and resolutions. Results match. The harness also
asserts no plane-buffer reads when all planes are disabled. Its source-level
load-site visits fall from 7,032,766 to 3,669,523. Those instrumentation counters
do not count emitted machine loads: the compiler may already avoid some unused
loads. No machine-load, game-speed or bus-bandwidth reduction is claimed.

Actual ARM memory, IRQ, beam, colour-write and ten-frame PCM comparisons also
match the reference. The hardware profile recorded no collision samples. This candidate was not
run as a hardware speed test or promoted: it does not address the measured
Banshee hotspot. Zero samples do not prove that these routines are never called.

[Evidence](remaining-costs/) includes diagnostic sources, source differences,
checks and physical logs; build scripts require the prepared workspace.

## Remaining scanline work

A second 6,000-frame diagnostic samples approximately one in 64 calls from
frame 3,000 onward. These are extrapolated inclusive seconds in that section,
not additive wall-time percentages:

| Path | Estimated seconds | Samples |
|---|---:|---:|
| Sprite decisions and recording | 8.22 | 16,280 |
| Sprite DMA service | 3.27 | 69,340 |
| Display-window decisions | 0.78 | 26,886 |
| Palette recording | 0.22 | 14,908 |
| Sprite/playfield collisions | — | 0 |
| Playfield collisions | — | 0 |

The run retained reference pixels and guest execution results, completed all
PCM and restored/released Core1 cleanly. Its 35.98 FPS includes instrumentation.
The result directs the next candidate toward sprite recording, not a palette
cache or disabled-plane collision optimisation.

## Specialised sprite recording

A separate candidate handles unclipped, unmasked spans without collision
processing in loops specialised for one, two or four output samples per source
pixel. The original routine handles partial clipping, masks, collision-enabled
spans and other cases. It retains the original OR compositing and stops at the
same last nonzero source pixel. Guest sprite DMA and event timing are untouched.

500,000 sanitized native comparisons match every buffer word (including guards)
and the collision register. Cases cover random initial pixels, sprite numbers,
border overrides, clipping limits, scaling, masks, collision masks and initial
collision flags, plus zero and short source words. 121,567 cases enter the
specialised path. This establishes equivalence in that fixture, not speed.

The usual four ARM fixtures and PCM comparison pass. A new synthetic guest
program exercises the actual compiled recorder. PAL and NTSC runs each encounter
256 eligible sprite calls; candidate
and reference CPU state, RAM, final pixels and frame hashes match. These model
runs do not establish physical timing or performance.

Follow-up correction: that fixture used an eight-byte pointer-register stride
instead of four, exercising the even-numbered sprites rather than all eight as
originally intended. The attachment follow-up fixes the stride, enables attached
sprites and checks 512 eligible calls on both PAL and NTSC. The historical
fixture's narrower coverage must not be described as an eight-sprite test.

## Matched hardware results

The test order was reference, candidate, candidate, reference. Every run uses
6,000 guest frames, the same scripted inputs and Paula settings.

| Run | Emulated FPS | Audio late-submit gaps |
|---|---:|---:|
| reference-first | 36.939 | 2064 |
| candidate-first | 37.149 | 2057 |
| candidate-repeat | 37.153 | 2056 |
| reference-repeat | 36.920 | 2061 |

The paired gains are **0.57% and 0.63%**. They are small but repeat in both
orders. These are whole-run emulated FPS, not displayed FPS or an internal game
frame rate. Audio starvation persists; the gap counters and completed sample
counts do not establish audible quality.

All four runs match reference guest dispatch count, cycle count, final PC and
framebuffer. All 3,330,048 PCM sample frames complete with device error zero;
Core1 register/MMU/cache-witness restoration and owned-memory release pass.
Together with the two profilers, this investigation covers six complete physical
runs / 36,000 guest frames.

**Retain as a private experiment, not an installed default.** Subsequent
[Slam Tilt intro/table tests](SPRITE-WIDER.md) matched correctness but found no
performance gain. The installed normal/FPU pair remains unchanged. The disabled-plane
collision change also remains unpromoted. No firmware, release or GitHub upload
is part of this investigation.

Private test executables were removed after the runs. Core1 is free and installed
normal/FPU binary hashes were verified unchanged.
