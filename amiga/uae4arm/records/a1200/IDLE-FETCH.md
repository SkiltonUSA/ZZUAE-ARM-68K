# A1200 idle-fetch batching and ZZ9000AX comparison

Follow-up to [scanline profiling](SCANLINE-SPANS.md). These are private experiments;
the installed normal and optional FPU players retain their current implementation.

## Idle cycles between bitplane fetches

The candidate batches idle AGA FMODE 2 cycles in the tail of `update_fetch`.
It stops before the next DMA phase, fetch-unit boundary, display stop, output
flush or caller boundary. Pending mode changes, BPL1DAT writes and cycle-based
lines retain the original per-cycle path. DMA reads, guest time, collision data
and Copper/register ordering are preserved; this is not alternate-line drawing.

Two versions were tested: one limited to active display state and one allowing
the later stop states up to their next transition. Power-of-two shifts replace
integer division in the eligibility calculation. The existing bulk-fetch path
is unchanged.

A passive counter found 837,460 eligible starting positions among 40,091,005
tail-cycle positions in the later Banshee section under the restricted rule.
Summed candidate spans overlap; they must not be reported as cycles saved.

## Correctness checks

- Each version passed one million sanitized native comparisons of cycle state
  and callback event order against the extracted original per-cycle routine.
  The harness stubs fetch/flush callbacks; it is not a complete chipset model.
- Four actual ARM fixtures matched reference CPU state, RAM and pixels; a
  separate ten-frame audio fixture matched PCM for each batching version.
- All three 6,000-frame physical runs (counter, restricted, broader) completed
  with matching dispatch count, guest cycles, PC and final framebuffer. All
  3,330,048 PCM sample frames completed with device error zero. Core1 restored
  registers/MMU/cache witnesses and released its allocation.

## Banshee results

PAL A1200, interpreter020, fullscreen, Paula 27,710 Hz, identical scripted guest
input and 6,000 guest frames. These are whole-run emulated FPS, not displayed or
internal game FPS. The reference is the preceding scanline control run.

| Build | Elapsed seconds | Emulated FPS |
|---|---:|---:|
| Current reference | 162.391 | 36.948 |
| Restricted idle batch | 165.304 | 36.297 |
| Broader idle batch | 162.307 | 36.967 |

The broader version is only 0.05% above the reference, below a useful measured
gain from this single comparison. The restricted version is 1.76% below it.
Neither is promoted. Broader batching reports 2,091 late-submit gaps versus
2,064 for the reference, so it supplies no evidence of an audio improvement.
The instrumented counter run (36.260 FPS) is not a performance candidate.

## Per-application ZZ9000AX output

The separate AX host uses the unchanged reference ARM payload and 27,710 Hz
source PCM. It resolves a registered realtime stereo 16-bit ZZ9000AX AHI mode
and requests a 32,000 Hz hardware mixer; AHI resamples the source. It uses
three immutable playback buffers, interrupt-time scheduling and task-side
copies. This adapts the existing ZZSNES AX queue implementation. No global AHI
preferences are written and there is no fallback silently selecting Paula.

This is still ARM-to-68K-to-AHI-to-AX playback, not direct ARM-to-AX DMA.
Guest Paula synthesis and the emulation workload remain on Core1.

The native queue ownership/retirement/underrun checks passed. A 120-frame
hardware startup probe selected mode `cafe0000`, received 86 callbacks and
completed all 65,536 queued sample frames with no device errors and clean
teardown. Its guest PCM was silent; it proves device advancement, not audible
quality. The 6,000-frame gameplay run completed in 163.799 seconds: **36.630 emulated
FPS**, versus the preceding Paula reference's 36.948. This single pair shows
no throughput improvement. All 3,330,048 queued sample frames completed,
including 2,296,574 nonzero guest frames, with device error zero. It recorded
5,444 callbacks, 2,192 silence blocks and 1,957 starvation events: moving output
to AX did not eliminate the producer deficit. Final framebuffer, guest dispatch
count, cycles and PC match the reference; Core1 cleanup passed. No listening
acceptance was collected.

AX's host output can retain 16-bit samples, unlike this direct-Paula 8-bit path,
but that format difference does not cure late PCM production. The AX experiment
is not installed or exposed as a new launcher option. Both live and saved AHI
preference hashes remain unchanged after the test. Private test executables
were removed, Core1 is free and installed normal/FPU player hashes are unchanged.

AX starvation events and Paula late-submit counts describe different events
and must not be compared as equivalent audio-quality measurements.

[Evidence](idle-fetch/) contains source patches, diagnostic build scripts,
validation output and physical logs. Scripts depend on the prepared workspace.
No ROM or game media is included.
