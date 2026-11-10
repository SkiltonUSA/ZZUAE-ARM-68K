# Display decisions and sprite DMA slots

A private Banshee profile separates the remaining display-decision costs.
Bitplane fetches and sprite decisions dominate; final line bookkeeping is small.
This diagnostic does not establish a new speedup or an audio fix.

## Display-decision profile

The unchanged four-pixel AGA interpreter reference is instrumented only inside
`finish_decisions`. Approximately one in 64 calls is sampled after guest frame
3,000 of a 6,000-frame PAL A1200 run, with native fullscreen, Paula 27,710 Hz,
2 MiB Chip RAM and locked scripted input. All eight stages record 14,768 samples.

| Scope | Estimated seconds in profiled section |
|---|---:|
| Finish decisions, inclusive | 33.186 |
| Display-window decisions | 0.464 |
| Start/advance display line | 3.629 |
| Bitplane fetch decisions | 19.297 |
| Final fetch drain | 0.139 |
| Sprite decisions | 7.861 |
| Record line state and end counters | 0.979 |

The total includes its nested scopes. Instrumentation changes execution cost
and code layout; timings include waits. Do not sum these rows, convert them to
exact wall-clock shares or treat them as removable time. An empty timer scope
averages 6.06 ticks and is not subtracted. The eight diagnostic records remain
inside the existing profile area, before the JIT report.

Final record bookkeeping does not justify a broad line-cache rewrite here.
The bitplane path includes guest-visible DMA and shifter state; skipping it
on unpresented frames is not equivalent to skipping drawing. Earlier shift,
fetch-order and inlining experiments already failed their performance gates.

### Validation

- Two 16-frame actual-ARM fine-pixel/Copper fixtures match reference CPU, RAM,
  pixels and direct-frame hashes. Counters are inactive during these short runs;
  the physical run confirms activity beyond the warm-up boundary.
- The physical run completes 6,000 frames with 116,472,634 dispatches,
  814,003,022 guest cycles, PC `00029056` and guest hash `eef62420`, matching
  the reference. Final pixels also match.
- All 3,330,048 queued PCM sample frames complete, with 2,296,574 nonzero frames,
  device error zero and stopped status. There are still 2,140 late-submit gaps;
  this is not listening acceptance.
- Register/MMU/cache-witness restoration, SIMD checks, transport and owned-memory
  release pass. The instrumented 166.381 seconds is not a speed comparison.

## Sprite DMA slot candidate

`do_sprites`, called during line decisions, walks every position in its pending
range. Phases 0 and 2 perform DMA work; phases 1 and 3 do nothing. A private
candidate walks only the two active phases. It preserves the original partial
range guards, phase-zero DMA-state reset, callback order and final horizontal
position. It does not skip sprite fetches or sprite rendering.

The extracted reference and candidate functions match in 1,116,300 sanitized
comparisons, covering partial ranges, vblank boundaries and paired DMA-state
patterns. All 1,345,600 observed callbacks retain their order and input state.
Actual ARM PAL/NTSC attached-sprite fixtures match CPU, RAM, pixels and frame
hashes. Memory, IRQ, beam and Copper-write fixtures also match. The generated
worker shrinks from 3,372 to 3,252 bytes; that is a code-size result only.

### Matched hardware result

| Build | Frames | Seconds | Emulated FPS | Audio gaps |
|---|---:|---:|---:|---:|
| Fresh reference | 6,000 | 162.499 | 36.923 | 2,069 |
| Active-slot iteration | 6,000 | 163.748 | 36.642 | 2,071 |

These are whole-run emulated FPS, not displayed or internal game FPS. Both use
the same Banshee media, scripted input, PAL A1200 interpreter and Paula settings.
The candidate measures **0.76% slower** in this single pair. This does not
establish a general regression, but supplies no reason to promote the change.
The installed player remains unchanged.

Both runs match the profile/reference guest signature and final pixel SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
All queued PCM completes, with identical nonzero counts, device error zero and
clean Core1/register/MMU/cache-witness teardown. Audio gaps remain; no audible
quality improvement is claimed.

## Outcome

The round covers **18,000 physical guest frames**: one profile and a fresh
reference/candidate pair. Temporary players were removed, Core1 is free and
installed normal/A1200/FPU hashes remain unchanged. No product version, firmware,
default or release changes follow from this result.

Removing empty loop iterations made the code smaller without improving this
workload. Further work should target measured bitplane/sprite processing costs
with a materially different approach, rather than repeating equivalent loop or
shift rewrites. This profile does not prove a hardware performance ceiling.

[Profile evidence](decision-costs/) and [candidate evidence](sprite-slots/)
include source changes, tests, build hashes, physical logs and checksums.
Scripts require the prepared development workspace; no ROM or game media is
included.
