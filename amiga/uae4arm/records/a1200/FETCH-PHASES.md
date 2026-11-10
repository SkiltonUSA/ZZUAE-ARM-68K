# AGA per-cycle fetch follow-up

The next useful optimisation target remains the fetch-loop/state boundaries,
not an isolated pixel-shifter rewrite or a larger audio buffer. This follow-up
separates flushing from bookkeeping and samples individual fetch cycles. It is
a diagnostic result, not a new speed improvement.

## Method

A private ARM32 player samples approximately one in 64 `one_fetch_cycle_0`
calls after guest frame 3,000. Compiler barriers surround timer reads. It runs
the same 6,000-frame Banshee PAL A1200/68020 interpreter sequence with native
fullscreen, Paula stereo at 27,710 Hz and fixed guest input.

Unlike [the previous profile](CYCLE-COSTS.md), sampling is selected within each
cycle rather than inherited from an enclosing `update_fetch` call. The new
scopes isolate the mode check, DMA dispatch/transfer, state updates, and
conditional pixel flush. This cross-check does not replace the earlier nested
Chip RAM measurements.

| Scope | Samples | Estimated seconds | Mean timer ticks |
|---|---:|---:|---:|
| Whole per-cycle function, inclusive | 758,624 | 38.010 | 260.96 |
| Mode-state check | 758,624 | 2.025 | 13.90 |
| DMA dispatch and transfer | 758,624 | 7.918 | 54.36 |
| State bookkeeping | 758,624 | 3.026 | 20.77 |
| Conditional pixel-shifter flush | 88,083 | 3.214 | 190.06 |
| Empty timer scope | 758,624 | 0.874 | 6.00 |

These sampled estimates include timing/recording overhead, waits and overlapping
scopes. Do not add the rows, subtract them from production runtime, or compare
the inclusive total directly with the differently instrumented earlier build.
Instrumentation also runs selection branches on unmeasured calls.

Flushing is comparatively costly when called but occurs in only part of the
sample. The aggregate DMA dispatch/transfer scope is larger. The mode check
and counter/state work are smaller individually. This does not establish
instruction-cache misses or prove which ARM instructions should be removed.

## Correctness and audio

- Actual ARM PAL graphics and Copper fixtures match reference CPU/RAM/pixels.
  Their short duration leaves warm-up counters inactive; hardware verifies that
  the profile becomes active later.
- The physical run retains 116,472,634 CPU dispatches, 814,003,022 guest cycles,
  final PC `00029056` and the reference framebuffer SHA256
  `78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
- All 3,330,048 queued PCM sample frames are submitted and completed with
  device error zero. There are **2,131 late-submit gaps**: the audio deficit
  remains. Completed delivery is not continuous playback or listening approval.
- Register/MMU/cache witnesses, SIMD checks and owned-memory release pass.
- The instrumented run takes 169.978 seconds, or 35.299 emulated FPS. This is
  not a candidate FPS result and must not be advertised as a regression in the
  installed player.

## Decision

Keep the installed interpreter and audio configuration. No candidate is promoted
and no ZZUAE release changes. The earlier audio-only and doubled-buffer tests
already showed that removing presentation or enlarging buffers does not cover
the sustained emulation shortfall.

A subsequent implementation should work across fetch-loop iterations: retain
state in locals only where callbacks cannot change it, and bound any combined
work at DMA stop, mode-change, Copper and output/collision-observation points.
The existing bulk path already handles eligible spans, so a new path must show
which additional spans it can handle safely. Preserve every guest-visible DMA
read, register side effect, collision result and final shift-register state.

This is a larger change with a correctness burden, not justification for another
unmeasured local rewrite. The rejected dispatch, guard, shifter, scroll-cache and
sprite experiments remain rejected. There is no measured gain from this round.

[Source patch, build hashes, ARM checks and physical evidence](fetch-phases/).
The diagnostic scripts require the prepared workspace. No firmware, ROM or game
media is included; normal/FPU installed hashes are unchanged.
