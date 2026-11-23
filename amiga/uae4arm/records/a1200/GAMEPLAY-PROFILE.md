# A1200 gameplay profiling

Physical A4000TX / ZZ9000 investigation, using the 0.6.0-dev interpreter build
with NEON conversion and inline Chip RAM reads. The installed interpreter
remains the default. No firmware change is involved.

## Workload and measurement

Banshee's playable demo runs for 6,000 guest frames with the same deterministic
input sequence as the [earlier comparison](PERFORMANCE.md). Profiling starts at
frame 3,000, excluding loading and concentrating on the flying scene. Settings:
A1200, Kickstart 3.1, 2 MiB Chip RAM, PAL, native fullscreen, sound output off.
The emulated audio hardware still runs when output is off.

The first diagnostic samples approximately one in 256 interpreter dispatches
with a seeded pseudorandom selector. Its stage intervals do not overlap:

| Sampled dispatch stage | Share |
|---|---:|
| Advance chipset events | 62.01% |
| Execute 68020 opcode, including its memory/device accesses | 20.06% |
| Special service: interrupts, Copper and other CPU flags | 12.92% |
| Dispatch bookkeeping | 5.01% |
| JIT validation | 0% |

Explicit Copper service accounts for 1.90% **inside** special service, and STOP
waiting accounts for zero in these samples. Do not add that Copper figure to
the table. Copper and other chipset work can also occur through other paths.
Event advancement includes callbacks such as drawing/presentation and audio;
it is not a measurement of scheduler overhead alone.

The profile contains 302,101 samples from 76,945,079 gameplay dispatches.
Clock reads, sampling and code layout affect timing; these are diagnostic
proportions, not an exact wall-clock decomposition or performance gain. The
profiled run took 198.19 seconds overall. Its final CPU dispatch count, cycle
count, PC and pixels matched the uninstrumented reference. Core1 restoration
and allocation release passed. A bridge timeout while printing the long log
was resolved by reading the completed log as a file; the emulator had exited.

This evidence prioritises chipset/event work. It does not support enabling the
slower partial JIT or claiming that all remaining time belongs to instruction
execution.

## Chipset breakdown

A second diagnostic samples approximately one in 64 calls to each selected
function, again only from frame 3,000. Sampled timer ticks are scaled by 64 and
the hardware timer calibration (approximately 333.33 MHz), then divided by the
116.03-second gameplay interval. These estimates are inclusive and overlap.

| Instrumented path | Estimated gameplay share |
|---|---:|
| Complete scanline handler (`hsync_handler`) | 63.2% |
| Bitplane fetch decisions (`decide_fetch`) | 18.1% |
| Audio hardware update (`update_audio`) | 4.0% |
| Scheduled blitter handler | 2.2% |
| Copper update (`update_copper`) | 2.1% |
| Disk hardware update (`DISK_update`) | 1.8% |

For example, a scanline can include bitplane fetch, Copper, audio and rendering.
**Do not sum these percentages.** The blitter row measures its scheduled handler,
not every possible forced-completion path. This profile also preserved the exact
final CPU state and frame hash and released Core1 cleanly.

The evidence points to scanline/bitplane processing before another CPU translator
change. The previous rendering improvements remain useful, but neither the CPU
opcode stage nor the measured Copper path alone explains the remaining slowdown.

## Candidate correctness gates

The no-event shortcut calls the original cycle service unless all four
conditions hold: the active service is `do_cycles_cpu_fastest`, its budget is
zero, no host synchronisation is pending, and the next guest event is strictly
later than this instruction's cycle advance. Only then does it add to
`currcycle` directly. Due events, alternate services and special budgets retain
the original implementation.

A native comparison exercised 100,000 randomised event-boundary, clock-wrap,
budget, synchronisation and alternate-handler cases under address/undefined
behaviour sanitizers. Actual ARM memory, IRQ, beam and CPU colour-write fixtures
matched the reference CPU state, RAM, pixels and frame hashes.

A second candidate compiles only `custom.cpp` with `-O3` instead of `-O2`.
Its source and emulated timing are unchanged; the same four ARM comparisons
passed. This targets the hot chipset module, unlike the earlier unsuccessful
`-O3` experiment on the CPU opcode module.

The diagnostic and candidate source differences, executable hashes, native
comparison fixture and ARM comparison records are in [gameplay](gameplay/).
These are experiment records, not enabled product patches.

## Matched candidate results

A fresh uninstrumented reference was run after the candidates to check drift.
All runs completed 6,000 frames; the gameplay interval is frames 3,000–6,000.

| Build | Whole-run emulated FPS | Gameplay emulated FPS | Gameplay change |
|---|---:|---:|---:|
| Current interpreter, fresh reference | 31.76 | 26.79 | — |
| No-event cycle-service shortcut | 31.93 | 26.91 | +0.44% |
| Chipset module `-O3` | 31.48 | 26.51 | −1.04% |

The fresh reference closely matches the prior 31.73 / 26.77 FPS repeat.
All candidates and both profilers reached identical CPU diagnostic results and
final frame hashes, with clean Core1 restoration and memory release. Across
this investigation, five complete hardware runs covered 30,000 guest frames.

**Neither candidate was promoted.** The shortcut's single-run gain is marginal
and does not yet justify an installed-code change; the compiler candidate
regresses. The installed 0.6.0-dev normal and FPU players remain unchanged, with
the 68020 interpreter default. Private test executables were removed after the
runs. No new speedup is claimed for the installed application.

[Machine-readable run results](gameplay/results.json).

## Scanline and fetch follow-up

A third diagnostic completed the same 6,000-frame hardware sequence with exact
final CPU/pixel agreement and clean teardown. Timers and counters cover frames
3,000–6,000; timers sample approximately one in 64 calls. Instrumentation slows
the run, so its 117.41-second gameplay interval is not a candidate benchmark.

| Path | Estimated inclusive gameplay share |
|---|---:|
| Scanline completion (`hsync_handler_pre`) | 42.1% |
| Finish display decisions | 29.2% |
| Sprite decisions | 6.8% |
| Prepare next scanline (`hsync_handler_post`) | 6.4% |
| Bulk bitplane fetch | 2.3% |
| Reset display decisions | 1.2% |

These sampled estimates overlap and have sampling variation; do not sum them or
subtract tables from different diagnostic runs as an exact decomposition.

Of 883,597 bulk eligibility checks, 844,775 passed (95.6%). Actual batching ran
765,004 times, all in AGA 64-bit fetch mode; another 79,771 eligible spans were
too short. Playfield stop state blocked 32,800 checks and cycle-based accuracy
blocked 6,038. Rejection reasons can overlap. DMA-off, phase, bad-mode and plane
count checks recorded no rejections in this workload.

The bulk path handled 70,558,976 fetch cycles; preparation and trailing loops
still executed 8,390,019 and 40,091,005 per-cycle steps. Bulk fetching already
works effectively. Removing accuracy checks or rewriting the bulk path alone
is unlikely to address most of the remaining cost. The next candidate targets
AGA pixel extraction used by the per-cycle output path, preserving DMA and
mid-line register scheduling.

[Exact counters and timer estimates](gameplay/fetch-profile-fetch-analysis.json),
[source changes](gameplay/fetch-profile.patch) and
[hardware log](gameplay/fetch-profile-run.log).

## Per-cycle candidates

Two independent candidates retain the interpreter and the original event/DMA
schedule:

* **32-bit AGA span extraction:** replaces a variable 64-bit shift with bounded
  32-bit extraction and avoids reading the upper word when the span does not
  reach it. The native comparison covered 4,456,448 cases: shifts 0–63, widths
  0–16, random input words, with address/undefined-behaviour sanitizers. ARM
  memory, IRQ, beam and colour-write fixtures matched. The 6,000-frame hardware
  run also matched exactly, but gameplay measured **26.71 versus 26.79 FPS**
  (−0.29%). This candidate is not enabled.
* **Fetch-order lookup:** replaces nested plane-selection switches with a
  16-byte lookup table, preserving the 2/4/8-plane fetch orders, idle phases
  and reserved one-plane behaviour. All 256 phase/sequence comparisons passed
  under sanitizers, as did the four ARM fixtures. The generated FMODE2
  per-cycle routine shrank from 7,436 to 2,504 bytes; this is a code-size result,
  not a speed claim.

Source differences and correctness records are retained in [gameplay](gameplay/).

The fetch-order candidate completed the matched hardware run with identical
CPU/pixel results and clean teardown, but measured **26.43 gameplay FPS**
(−1.36% versus the 26.79 reference). Neither per-cycle candidate is enabled.
The follow-up adds three complete hardware runs / 18,000 frames; combined with
the first profiling series, eight runs covered 48,000 guest frames. Installed
normal/FPU binaries were checked unchanged and private executables removed.
Core1 is free. No firmware change, GitHub push or release was made.

## Next investigation: avoiding repeated rendering

The supplied Ghouls 'n Ghosts patch transcript (2026-11-09) suggests a more
substantial experiment than another instruction substitution: count unchanged
rendered spans and the cost of detecting them before adding a persistent cache.
The existing presentation converter reuses vertically repeated rows only
within a frame. Reusing work across frames requires validity checks for source
pixels, palette/register changes, sprites, display mode and output format.
Cached pixels must live in private RAM; the current bitmap grant/ownership
contract still applies, and skipping writes to a different back buffer requires
separate proof that its contents are current.

Guest CPU/chipset execution, blitter memory effects and completion timing must
continue. Host drawing batches can be combined only where the guest-visible
result and event order stay identical. The transcript's sprite interpolation,
object movement and three-vblank cap changes are game-specific patches, not
safe generic emulator optimisations. Its reported gains are not ZZUAE results.

Measure cache hit rate, comparison/invalidation overhead and end-to-end FPS on
Banshee plus a scrolling/Copper-heavy scene before retaining an implementation.
Sound-enabled acceptance remains separate; the present tests used sound output
off and do not resolve the previously recorded audio gaps.

[Rendered-output reuse follow-up](RENDER-REUSE.md) measures exact repeated pixels
and tests a separate conversion cache without skipping frame delivery.

The [compositing follow-up](COMPOSITING.md) separates palette, sprite and pixel
work before final display conversion.
