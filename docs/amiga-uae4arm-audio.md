# ZZUAE audio

The Sound selector offers **Off**, **Paula direct**, and **AHI**. This is host
output selection: all four guest Paula channels are still emulated on Core1.
Paula direct uses the Amiga's native audio sockets; AHI uses the configured unit
0 output (which can be ZZ9000AX). No AHI preferences are rewritten.

| Output | Format | Delivery |
|---|---|---|
| Off | No PCM | Guest Paula DMA and interrupts remain active |
| Paula direct | 8-bit stereo, about 27.7 kHz PAL / 28.0 kHz NTSC | `audio.device`, two allocated channels, Chip RAM buffers |
| AHI | 16-bit stereo, 32 kHz | `ahi.device` unit 0, linked asynchronous requests |

Paula direct is mixed PCM from the emulated Paula, played through native Paula;
it does not forward guest register writes to the physical custom chips. It uses
period 128 and selects the mixer rate from the host PAL/NTSC audio clock. Channel
allocation uses low priority and a nonblocking request; unavailable output is
reported, rather than falling back silently. Existing device configuration and
system filter settings are preserved.

Sound-enabled runs use audio consumption to pace PAL emulation at approximately
50 guest frames per second. The display setting can independently select 25 or
30 presented frames per second, reducing host drawing work while retaining normal
audio/game timing. 50/MAX delivers every guest frame. With sound Off, the existing
25/30/50/MAX pacing still applies to the whole lockstep guest. Capture-only mode
has no audio output. The current interpreter may still fall behind real time with a
heavy workload; this implementation does not time-stretch or conceal underruns.

## Implementation

Pinned UAE4ARM's integer stereo mixer produces 256-frame chunks. The adapter
batches these into 1024-frame blocks in a four-slot queue within the existing
32 MiB owned allocation. Shared counters and interleaved PCM use big-endian
encoding; separate cache lines hold producer/consumer counters. The ARM waits
when full and checks cancellation. Only complete blocks are published.

The 68K main process copies the occupied snapshot into the available part of a
bounded local queue, before servicing graphics. It publishes the completed
batch and wakes the audio process once; unpublished slots remain invisible. A
separate DOS audio process owns the device, messages and playback buffers. It
prebuffers two blocks and queues two stereo playback requests. The audio process
runs at priority 5 and sleeps between buffer events. AHI retains its
linked predecessor until the successor has been submitted. Paula uses two
planar Chip RAM buffers per stereo pair, with native channel ownership managed
by `audio.device`. Stop drains queued blocks, then aborts outstanding device I/O
if needed; buffers are freed only after completion. Core1 teardown and
reset-before-free remain unchanged. The final incomplete PCM block (less than
1024 frames) is discarded when the guest stops.

Initial sound uses the unfiltered, noninterpolated integer mixer. Analog filter
emulation, audio interpolation controls, volume/mixing UI and rate selection
remain future work. The audio mixer uses no VFP/NEON instructions or firmware audio services.
The display renderer uses NEON separately.
The worker design is adapted from the project's ZZDosBox audio implementation.

Device API references: [AmigaOS audio.device](https://wiki.amigaos.net/wiki/Audio_Device)
and [AHI device](https://wiki.amigaos.net/wiki/AHI_Device).

## Verification

Native tests cover signed PCM byte order, stereo layout, ring wrap/full bounds,
shared-memory bounds and launcher sound-mode persistence/command generation.
An ARM instruction-model ROM programs real emulated Paula DMA for two distinct
stereo tones: 10 guest frames produced 6144 stereo PCM frames, 6138 nonzero.
The silent OCS red-frame regression and shared framework suites also passed.
These checks are not evidence of audible playback on the physical Amiga.

Physical A4000TX runs completed with exit 0, device buffers drained, ARM
register/MMU/cache restoration passing and owned memory released:

| Test | Guest / displayed frames | Completed stereo PCM frames | Nonzero frames | Queue-gap observations |
|---|---:|---:|---:|---:|
| Original diagnostic tone, AHI | 500 / 250 | 319,488 | 319,482 | 2 |
| Original diagnostic tone, Paula (installed build) | 500 / 250 | 276,480 | 276,475 | 1 |
| Alien Syndrome title sequence, AHI (installed build) | 3,000 / 1,500 | 1,922,048 | 201,057 | 44 |

The final game run took 60.660436 seconds for 3,000 guest frames. All submitted
PCM frames completed without device errors. The gap counter records occasions
when the previous request had already completed before the next was submitted;
it is not a measurement of audible gap duration. Raising audio-process priority
from 0 to 5 did not materially reduce the game gap count (42 versus 44). Sound is
functional, but uninterrupted playback has not been established for every workload.
Listening remains required to assess speaker routing, crackle and audio quality.

Initial Alien Syndrome tests with read-only DF0 stopped at its startup Protect
command and produced silent PCM. Temporary writes allow startup to continue;
they modify a private RAM copy, never the supplied ADF. The title-sequence run
used this mode plus the existing scripted left-mouse press. It is not full-game
compatibility or listening acceptance. Logs and build records live in
`amiga/records/2026-10-26/uae4arm/audio/`.

## Joystick

The launcher selects Off or Amiga port 2, and provides a separate Joystick test
window with live Up/Down/Left/Right/Fire indicators. It uses `lowlevel.library`
V40 and does not change device detection modes. Version 0.4.1-dev maps three fire buttons to guest port 2: Red -> Fire 1,
Blue -> Fire 2, Green -> Fire 3. The tester shows oval direction indicators and
three circular fire indicators, green when pressed. A normal joystick report
supplies Red/Blue; Green is read only for a detected game controller. This does
not add electrical/protocol support for arbitrary three-button controllers.
See the [ReadJoyPort autodoc](https://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_3._guide/node0468.html).

The 0.4.1 update also corrects a reversed left/right event mapping. ARM-model
checks verify all four directions, guest Fire 1 via CIA, Fire 2/3 via POTGOR,
and release of all three buttons on focus loss.

Arrow keys and left Alt remain available. Keyboard and physical stick states
are combined so a release from one source cannot cancel a held input from the
other. Losing window focus releases guest input; physical polling resumes when
the emulator window becomes active. The tester stops when a player is launched.
A physical movement/button acceptance check is still required when someone is
present at the Amiga.

The actual MUI sound cycle was exercised through Paula direct, Off and AHI.
Save and reopening retained AHI, port 2 and 25 FPS. The tester window opened,
polled without blocking the UI and closed automatically on Start. A subsequent
GUI Stop during AHI playback exited cleanly with all queued audio completed.

## 0.5.4 development follow-up

Removing redundant full-brightness multiplications and per-vector byte-order
branches from the NEON renderer reduced late AHI queue observations from 36 to
0 in a matched 3,000-frame Alien Syndrome startup/title run. Guest CPU state and
PCM counts matched. The larger four-block startup prebuffer also recorded zero,
with no demonstrated advantage; it was not retained. The normal two-block
prebuffer remains about 64 ms at 32 kHz, avoiding added startup latency.

The accepted host change drains a bounded occupied batch before graphics and
signals once. It preserves device request linking, PCM contents, 32 kHz output
and cancellation/drain rules. Native tests execute the actual drain function
with empty/full rings, index wrap, consumer progress and invalid shared counts.
Measurements and longer-run results are in [the follow-up report](amiga-uae4arm-054.md).
Queue observations do not prove audible quality; listening acceptance remains required.
