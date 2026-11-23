# A1200 rendered-output reuse investigation

The Ghouls 'n Ghosts game-patch transcript prompted a separate experiment on
ZZUAE's host presentation path. The game, interpreter and chipset schedule are
unchanged. These are private experiments against the existing 0.6.0-dev build,
not enabled release features.

## Workload

The same Banshee demo sequence, PAL/A1200/68020 interpreter, native 320×256
fullscreen, sound output off, 6,000 guest frames. Diagnostic counts cover only
frames 3,000–6,000. Output-disabled sound still emulates the audio hardware.
See [the matched benchmark method](PERFORMANCE.md).

## Exact pixel comparison

The diagnostic compares the completed 640×256 RGB565 source with the previous
frame. Each row is also divided into twenty 32-source-pixel spans. It counts
both all source pixels and the even pixels used by native 320-wide conversion.
No probabilistic hashes are used for cache eligibility. Previous pixels are
updated on every comparison; the first frame is cold.

| Measurement | Exact count | Share |
|---|---:|---:|
| Identical complete frames | 782 / 3,000 | 26.07% |
| Identical rows | 400,284 / 768,000 | 52.12% |
| Identical 32-source-pixel spans | 9,440,771 / 15,360,000 | 61.46% |

All-source and visible-pixel counts agree in this workload. These figures include
borders and static interface areas; they do not mean that half the total emulator
work can safely be skipped. Final pixels already include sprites, scrolling,
palettes and Copper effects, but guest execution remains necessary.

The exhaustive scanner took **24.73 seconds** over the 3,000-frame interval.
Direct conversion including that scanner took 30.17 seconds; the remaining
5.44 seconds includes pixel conversion, display writes and mapping overhead.
The diagnostic is deliberately exhaustive and is not a performance candidate.
Its final CPU and image results match the reference, and hardware teardown passed.

## Conversion-cache candidate

The candidate keeps converted rows in private runtime memory. Each comparison
checks four 32-bit words at a time and stops at the first difference. Native
320-wide output masks the unused odd pixels; 640-wide output compares all pixels.
On a miss, conversion uses the existing NEON/scalar routine and remembers the
source. Unsupported widths use the original uncached conversion path.

Width, pixel format or PAL/NTSC source-height changes invalidate the cache. Every
grant still receives the entire output frame, including the ownership-challenge
locations. No display address is cached, no bitmap is read back, and the normal
handshake, snapshot handling, cancellation and input polling remain in place.

The initial static cache exceeded the existing BSS/stack boundary and was
rejected by the linker before hardware use. The candidate instead allocates
approximately 960 KiB from the already reserved runtime heap. Allocation failure
uses the original conversion path. The 64 MiB Exec allocation and 32 MiB
translation cache are unchanged.

Native sanitized tests cover cache hits/misses, changed visible/unused pixels,
last-pixel boundaries and width/format/height invalidation. Four ARM guest-state
comparisons match the reference. Direct ARM conversion checks cover both pixel
formats, repeated frames, multiple output sizes, row padding, snapshots, nonce
rejection, mapping collisions, cancellation and SIMD register preservation.

## Evidence

[Exact counts and timers](reuse/profile-repeat-analysis.json),
[diagnostic hardware log](reuse/profile-run.log),
[conversion-cache patch](reuse/row-cache.patch),
[cache implementation](reuse/row_cache.h),
[direct ARM checks](reuse/check-cache-direct.log) and
[build hashes](reuse/builds.json).

An identical-frame presentation skip is deliberately excluded: presentation
contributes to wall-clock pacing, and skipping its handshake without independent
guest pacing could accelerate simpler games. The measured candidate reuses only
conversion results, preserving that pacing.

## Hardware result and decision

| Build | Whole-run emulated FPS | Gameplay emulated FPS |
|---|---:|---:|
| Existing interpreter reference | 31.76 | 26.79 |
| Row conversion cache | 31.63 | 26.63 |

The cache reduced actual NEON row conversions from 1,536,000 to 398,141 over
the whole sequence (74.08% fewer, including loading). All 6,000 frames were
still delivered; all 6,000 SIMD checks passed. Yet gameplay was **0.61% slower**
in this comparison. This is no demonstrated speed gain, so the candidate is
**not enabled**. Comparison, source retention and extra memory traffic cost more
than the saved conversion work in this workload.

Both new hardware runs completed 6,000 frames, with exact CPU diagnostics and
final RGB565 SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
Register/MMU/cache restoration and owned-memory release passed. The additional
ARM test alternated changed and unchanged source colours without changing output
dimensions; both pixel formats and guard checks passed.

This rejects this particular conversion cache, not all renderer caching. A
future candidate would have to skip more expensive work before final pixel
conversion, while validating bitplanes, palette/Copper changes, sprites and
line state. It must preserve guest hardware side effects. Simply adding a
cache after the existing NEON conversion pipeline is not enough.

Installed normal/FPU binaries are unchanged; the interpreter remains default.
Private test executables were removed and Core1 was checked free. No GitHub push,
release or firmware change. Audio stability is not established by these tests.

[Matched results and conversion counters](reuse/results.json),
[changed-source ARM checks](reuse/check-cache-changes.log),
[final installation checks](reuse/unchanged-installed-players.json).
