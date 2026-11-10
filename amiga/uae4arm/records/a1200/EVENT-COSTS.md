# Scheduled events and scanline phases

Two physical diagnostics narrow the remaining A1200 optimisation target to
display-state completion and line setup. Event scheduling itself is much smaller.
These are profiling results, not a new speedup or audio fix. The installed
normal/FPU players remain unchanged.

## Method

Each private build starts from the current four-pixel AGA interpreter reference.
It runs the same 6,000-frame Banshee sequence with PAL A1200/68020, 2 MiB Chip RAM,
native fullscreen, Paula 27,710 Hz and locked scripted input. Approximately one
in 64 calls is sampled after guest frame 3,000. Timer reads have compiler memory
barriers; estimates scale accumulated ticks by 64 and the calibrated timer rate.

The profiles run separately. Timers include nested work and waits, and affect
code layout and execution cost. Their estimates overlap and must not be added
or presented as exact wall-clock percentages or potential saved time.

The eight 16-byte diagnostic records fit the existing profile area and end before
the JIT report. No runtime allocation, firmware, DMA scheduling or guest-cycle
policy changes are involved.

## Primary scheduled callbacks

| Scope | Samples | Estimated seconds in profiled section |
|---|---:|---:|
| Scanline callback | 14,742 | 50.260 |
| Audio callback | 58,936 | 5.401 |
| Blitter callback | 3,178 | 2.578 |
| Event scheduling | 83,579 | 1.006 |
| CIA callback | 81 | 0.020 |
| Miscellaneous callback | 49 | 0.003 |

No samples were recorded at the scheduled Copper or DMA callback entries.
That does **not** mean those devices do no work: direct calls and work nested
inside other callbacks are outside those separate entry-point measurements.

The result supports looking inside scanline work before rewriting the event
queue. The scheduled blitter handler also costs far less here than the scanline
callback; earlier frequent empty service calls were not blitter arithmetic.

## Scanline phases

| Scope | Samples | Estimated seconds in profiled section |
|---|---:|---:|
| Line completion, inclusive | 14,775 | 42.116 |
| ↳ Copper catch-up | 14,775 | 0.224 |
| ↳ Finish display decisions | 14,775 | 32.275 |
| ↳ Record/draw line | 14,775 | 2.376 |
| ↳ Device servicing | 14,775 | 6.306 |
| Next-line setup, inclusive | 14,821 | 7.518 |
| Frame completion | 39 | 3.033 |

Indented rows are inside line completion. The frame-completion estimate has
only 39 samples and deserves less weight. An empty timer scope recorded a mean
of 7.76 ticks across 14,775 samples; it is not subtracted from the other stages.

`finish_decisions` includes display-window decisions, pending bitplane fetches,
final shifter draining, sprite decisions and recording line state. It is not
just conversion of finished pixels. Device servicing includes IDE/stop checks,
floppy service and audio service. Next-line setup includes CIA work, DMA setup,
blitter slowdown accounting and resetting display decisions.

These results prioritise separating those costs before choosing another local
shortcut. Changing only presentation or increasing audio buffers cannot be
assumed to remove the measured guest-chipset work. No proposal here drops DMA,
collision data, Copper writes or emulated cycles.

## Validation and limits

- Both profilers match the reference in 16-frame ARM fine-pixel and Copper
  comparisons, including all acknowledged direct-frame hashes. Counters remain
  inactive during this warm-up test.
- A separate actual-ARM positive control forces scheduler calls after the
  warm-up boundary and records 15 samples, proving the counter path is active.
- Both physical runs finish all 6,000 frames with the reference dispatch count,
  guest cycles, PC, guest hash and final framebuffer hash.
- Each delivers all 3,330,048 PCM sample frames, with 2,296,574 nonzero frames and
  device error zero. Late-submit gaps remain: 2,082 and 2,157. This is not listening
  acceptance or a comparison of audible quality.
- Register/MMU/cache-witness restoration, SIMD checks, transport and memory
  release pass. Instrumented durations are 165.668 and 167.008 seconds; neither
  is an uninstrumented performance comparison.

The round covers 12,000 physical guest frames. Temporary diagnostic players were
removed, Core1 is free and installed normal/A1200/FPU hashes are unchanged.
No new product version or release is warranted by profiling alone.

[Evidence](event-costs/) contains source patches, timer definitions, build hashes,
model comparisons, physical logs, analyses and cleanup checks. No ROMs or disks
are included. The scripts use the prepared development workspace.
