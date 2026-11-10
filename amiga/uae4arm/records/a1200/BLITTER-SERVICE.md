# Zero-cycle blitter service

The [service counters](SPECIAL-SERVICE.md) found that 83.16% of Banshee's later
special-service calls entered with only `SPCFLAG_BLTNASTY` set. Those counts
identified a frequent call, not actual blitter execution.

## Finding

The A1200 accelerated interpreter path advances instruction cycles first, then
calls `do_specialties(0)`. The handler's blitter loop requires `cycles > 0`, so
that loop cannot execute at this call site. With BLTNASTY as the only flag, the
handler performs flag checks and clears an already-clear END_COMPILE bit before
returning. It neither advances chipset cycles nor runs blitter arithmetic.
Actual blitter work still runs through the existing scheduled handlers; this
finding concerns the additional zero-cycle service call only.

A separate sampled profiler reported no nonzero stages for `blitnasty()`, its
channel-counting loop or the nested event advance during the later gameplay
period. A positive-control ARM test forces post-warm-up calls and records 15
samples, proving the counter path is active. This absence of measurements must
not be described as a measured zero execution cost for the whole handler.

The profiler run matches reference guest state and final pixels, completes all
PCM delivery and restores/releases Core1. Its first framebuffer transfer received
an incomplete bridge response; a separate retry retrieved the matching capture.

## Candidate

Only the zero-cycle call site changes:

```cpp
if (regs.spcflags && regs.spcflags != SPCFLAG_BLTNASTY && !regs.halted)
    do_specialties(0);
```

BLTNASTY remains pending. Every combined flag value and every other service flag
still reaches the original handler. Positive-cycle callers remain unchanged.
This does not enable immediate blits, drop cycles or alter DMA scheduling.

## Correctness checks

- Four actual ARM comparisons cover memory, interrupts, beam reads and Copper
  colour writes, including a nonempty PCM comparison. CPU state, RAM and output
  match the reference.
- Direct calls to the reference handler confirm that zero cycles with BLTNASTY
  alone preserve the flag and register state.
- A generated guest program starts a priority blit. The reference makes 1,422
  blitter-only service calls; the candidate makes none. Guest CPU state, RAM and
  pixels are identical.
- Fine-pixel and Copper model comparisons validate the separate profiler build.

## Physical comparison

The first matched pair uses 6000 frames per run, PAL A1200 interpreter, native
fullscreen, Paula audio and identical scripted Banshee inputs. Private test hosts
suppress external gameplay input; installed controls are unchanged.

| Run | Emulated FPS | Audio late-submit gaps |
|---|---:|---:|
| Fresh reference | 36.934 | 2066 |
| Candidate | 37.555 | 2053 |
| Candidate repeat | 37.581 | 2059 |
| Reference repeat | 36.907 | 2069 |

The paired gains are **1.68% and 1.83%**, repeated in opposite orders. This is
whole-run emulated FPS, not displayed FPS or the game's internal frame rate.
It demonstrates a repeatable gain in this workload, not a universal gain.

All four runs match 116,472,634 dispatches, 814,003,022 guest cycles, PC `00029056`
and framebuffer SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
All 3,330,048 queued PCM frames complete with device error zero. Audio gaps
remain; no audible-quality improvement is claimed. Register/cache-witness
restoration and owned-memory release pass.

The candidate is retained privately. Subsequent [wider Slam Tilt checks](BLITTER-WIDER.md)
pass correctness but show no useful speed gain, so it remains unpromoted.
The four performance runs and one profiler run here cover 30,000 physical
guest frames. Temporary players were removed, Core1 is free, and installed
normal/A1200/FPU hashes remain unchanged. No firmware, product version or release
has changed.

[Evidence](blitter-service/) contains the patches, diagnostic sources, model
comparisons, build hashes, physical logs and cleanup checks. No game or ROM
media is included.
