# Fetch-loop call boundaries

This follows [per-cycle profiling](CYCLE-COSTS.md), testing whether removal of
repeated call boundaries improves A1200 bitplane processing. The existing
interpreter, ChipRAM mapping, CPU/chipset timing, audio and presentation policy
remain the same. Neither candidate skips emulated cycles.

## Two code layouts

The reference has separate `one_fetch_cycle_fm0/1/2` functions. `update_fetch`
calls the appropriate function while preparing for bulk fetching and again in
the trailing per-cycle loop.

The first candidate directly invokes the existing always-inline cycle body at
both call sites. This removes the calls but duplicates the large cycle body.

The follow-up combines the preparation and trailing loops, with a local phase
flag. The original bulk block runs once at the first plane-zero boundary. Both
phases share a single inline cycle body. DMA/mode checks, fetches, output flushing
and end-of-line behaviour retain their source ordering.

| Fetch mode | Reference caller + helper bytes | Straight inline bytes | Shared-loop bytes |
|---|---:|---:|---:|
| 16-bit | 9,212 | 15,660 | 9,008 |
| 32-bit | 8,988 | 15,208 | 8,784 |
| 64-bit | 9,668 | 16,612 | 9,396 |

The separate cycle functions disappear from both candidates. Disassembly
confirms removal of the calls. This does not establish how many dynamic loads
or stores were removed, and no instruction-cache misses were measured.

## Correctness checks

Both candidates pass four ARM memory/IRQ/beam/colour-write fixtures and a
nonempty matching PCM comparison. Straight inlining also passes the PAL/NTSC
mixed fetch-mode, resolution and scroll fixture.

The shared-loop candidate passes 100,000 sanitized native comparisons of the
actual reference/candidate loop source with deterministic stateful callbacks.
Final state and complete callback traces match. Across both sides, cases invoke
the bulk path 1,118 times and the per-cycle path 3,916,470 times. This validates
control flow under those callbacks, not complete chipset emulation.

Additional PAL/NTSC ARM fixtures combine resolution/scroll/fetch changes with
bitplane DMA disable/restart and DDFSTOP changes mid-line. CPU state, RAM,
framebuffers and frame hashes match. All three mode-specific block-setup paths
are exercised.

## Physical comparison

Runs use the same 6,000-frame scripted Banshee sequence, A1200 interpreter, PAL
fullscreen and Paula audio. Only private test hosts suppress external gameplay
input; production input remains unchanged.

| Build | Whole-run emulated FPS | Change | Audio late-submit gaps |
|---|---:|---:|---:|
| Fresh reference | 36.931 | — | 2,063 |
| Straight inline | 35.961 | -2.63% | 2,164 |
| Shared-loop inline | 36.552 | -1.03% | 2,089 |

Both candidates fail the performance gate despite correct output. The shared
loop removes calls and slightly reduces compiled code size, but neither property
produces a speed gain in this comparison. No cache-miss cause is established.
These single comparisons do not establish a universal regression.

All three runs match guest dispatch/cycle counts, final PC, frame hash and captured
pixels. Each queues, submits and completes 3,330,048 PCM samples with no reported
audio error. Late-submit gaps remain; this is not an audio-quality improvement.
All runs pass cache-witness/register restoration and release owned memory.

Reject both candidates. Temporary players are removed, Core1 is free, and MD5
checks confirm the installed normal/A1200 and optional FPU players are unchanged.
No product version, release or firmware change.

[Source patches, ARM disassembly, fixtures and hardware logs](fetch-inline/).
