# A1200 PCM production and playback

The Banshee Paula gaps are principally a sustained emulation-throughput problem
in this measured workload. Larger audio blocks did not resolve them. Keep the
existing 1,024-sample blocks and interpreter default; no new audio fix is claimed.

## Method

Three private builds completed the same 6,000-frame Banshee demo sequence on
the physical A4000TX/ZZ9000: A1200/68020 interpreter, PAL, native fullscreen,
Paula stereo at 27,710 Hz, and deterministic guest input. The reference is the
installed 0.6.0-dev four-pixel AGA build with diagnostic counters added.
These are emulated-frame rates, not the game's internal or displayed FPS.

ARM counters measure intervals between complete PCM publication attempts and
time waiting for a full shared queue. Two banks cover the entire run and the
section beginning at guest frame 3,000. Timer conversion uses each run's
hardware calibration. The 68K records main-task audio-service intervals and
sampled queue occupancy; the audio worker and device submission remain unchanged.

The larger-block build uses 2,048 samples consistently on ARM and 68K. This also
doubles the two-block prebuffer from approximately 74 to 148 ms and the three-block
display-pressure threshold from 111 to 222 ms. It is a combined buffer-policy
experiment, not an isolated transfer-size measurement.

The audio-only diagnostic suppresses all intermediate drawing/presentation,
retaining guest CPU, chipset and audio execution plus a final display. It is
an upper-bound investigation of removing display work, not a usable player mode.

## Physical results

| Build | Elapsed seconds | Emulated FPS | Later PCM supply / playback demand | Presented frames |
|---|---:|---:|---:|---:|
| Reference, 1,024 samples | 162.87 | 36.84 | 62.36% | 2,350 |
| Larger blocks, 2,048 samples | 163.45 | 36.71 | 61.87% | 2,378 |
| Audio-only diagnostic | 154.38 | 38.86 | 66.32% | 1 |

In the later gameplay section, the reference takes **59.26 ms** on average to
produce a block containing **36.95 ms** of audio. It spends zero time waiting
for a full PCM queue in that section. The larger blocks take 119.45 ms to
produce 73.91 ms of audio, also with no full-queue waits. Removing intermediate
drawing reduces the 1,024-sample production interval to 55.72 ms, still too slow
for continuous playback at the unchanged sample rate.

All three runs queued, submitted and completed 3,330,048 stereo sample frames
(120.17 seconds at the device rate), with zero reported device errors. The
elapsed-time excess over that audio duration is 42.69, 43.28 and 34.21 seconds
respectively. These differences are not measurements of exact audible silence:
startup, drain and buffering contribute to the totals. The later producer
intervals independently show the sustained shortfall.

Reference host service intervals stayed below 24.46 ms; 97.95% were below 5 ms.
That does not prove every device deadline was met, but it does not support a
host polling delay as the main explanation for the measured sustained deficit.
Sampled empty-queue durations are approximate occupancy observations, not exact
underrun durations or a full decomposition of lost time.

The gap counter falls from 2,071 to 1,028 with larger blocks, while the block
count halves from 3,252 to 1,626. Normalised counts remain about 63.7% and 63.2%
of blocks. A lower raw gap count therefore does **not** establish improved
audio. No listening comparison was recorded. These are single diagnostic runs;
the 0.36% FPS difference is not a robust regression claim.

## Correctness and limits

- Native host-queue checks pass at both sizes: occupied spans, empty/full queues,
  wrapping, concurrent consumer progress and buffer allocation sizes.
- Ten-frame actual ARM instruction-model comparisons match reference CPU state,
  Chip RAM, pixels and PCM for all three diagnostic builds. These fixtures do
  not establish full-game equivalence.
- All physical runs complete 6,000 frames, 116,472,634 dispatches and 814,003,022
  diagnostic cycles, with final PC `00029056`. Register/MMU/cache restoration,
  witnesses and owned-memory release pass.
- Reference and larger-block runs have identical final pixels. The audio-only
  diagnostic differs in eight pixels at the top-left corner (x=0–5, y=0–1).
  Its final framebuffer is **not bit-identical**, despite the matching dispatch,
  cycle and PC results. The printed `UAE_MACHINE hash` hashes pixels, not CPU
  state; do not label its difference a CPU-state mismatch or claim complete
  hardware state equivalence. No full hardware PCM checksum was captured.

## Decision and next target

### ZZ9000AX output

Physical Paula playback and guest Paula emulation are separate. Selecting an
AHI mode backed by ZZ9000AX changes the output hardware; the emulator must still
execute the guest's Paula registers, DMA and mixing to generate its PCM.
The current ZZUAE AHI backend uses configured unit 0, which does not by itself
guarantee AX selection. Its 16-bit PCM path also avoids the direct-Paula backend's
conversion to signed 8-bit samples.

[Xanxi's XACP application model](https://github.com/Xanxi-Amiga/XACP-ZZ9000/blob/main/docs/XACP_V1_6_DEVELOPER_DOCUMENTATION.md)
places AHI playback on the Amiga side. The
[ZZ9000AX AHI driver](https://github.com/BlitterStudio/zz9000-drivers/blob/master/ahi/driver/zz9000ax-ahi.c)
includes a host mix-buffer transfer to the card. Choosing AX through AHI is
therefore distinct from a card-local ARM-to-AX PCM path. Such a path needs a
verified playback/buffer-ownership interface compatible with the installed
firmware and other audio clients; this investigation did not implement it.

AX output is a useful quality/transport comparison, but it does not remove the
measured producer shortfall. Compare devices at a matched sample rate before
claiming a performance difference. No AX hardware test, firmware update or
global AHI preference change was made in this investigation.

### Retained configuration

Do not promote either experimental policy. Larger blocks add buffering delay
without a demonstrated throughput or audio benefit. Suppressing the display
entirely still misses the necessary production rate. Reducing playback pitch
or changing the guest clock was not tested or applied.

The next performance investigation should return to scanline/display-decision
work in the chipset, guided by the [gameplay profile](GAMEPLAY-PROFILE.md), and
repeat these producer measurements after a correctness-preserving improvement.
That earlier profile used sound output off, so its percentages cannot be added
to or directly subtracted from these sound-enabled measurements. Further queue
servicing improvements may help short stalls, but cannot alone cover this
sustained production deficit.

Normal/FPU installed binaries remain unchanged. Private test executables were
removed after the runs and Core1 checked free. No firmware, media, guest timing,
sample rate or release was changed.

[Evidence](audio-pacing/) includes physical logs, analyses, model states, native
test results, diagnostic source patches and executable hashes. The archived
build/check scripts record the private experiment and require its prepared
workspace builds; they are not standalone release build commands.
