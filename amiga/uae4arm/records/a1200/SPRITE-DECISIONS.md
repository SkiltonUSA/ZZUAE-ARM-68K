# Sprite decisions and attachment flags

**Do not enable the attachment-word candidate.** It matched the reference's
results but ran 1.08% slower in the measured Banshee comparison. The installed
normal/FPU players and interpreter default remain unchanged.

## Where the time goes

A private diagnostic sampled approximately one in 64 calls after guest frame
3,000, with Paula audio enabled. It passed four ARM CPU/memory/beam/colour-write
fixtures before hardware testing. The clean 6,000-frame physical run matched
reference dispatches, cycles, PC and framebuffer, then restored and released
Core1 correctly.

| Timed path | Samples | Estimated seconds |
|---|---:|---:|
| Entire sprite decision | 16,242 | 9.756 |
| Display preparation | 11,996 | 0.690 |
| Candidate scan/sort | 11,996 | 0.603 |
| Record selected sprites | 11,996 | 7.787 |
| Nested pixel recorder | 95,968 | 4.177 |
| Sprite DMA | 69,303 | 3.179 |

Estimates scale sampled ticks by 64 and the calibrated hardware timer frequency.
They include instrumentation costs and overlap: pixel recording is inside
selected-sprite recording; preparation can call DMA. **Do not add these rows.**
The diagnostic's 35.69 emulated FPS is not an optimisation result.

Every sampled scan that passed the existing early checks produced sprites to
record. An additional empty-scan shortcut therefore lacks evidence for this
workload. Recording dominates these measured sprite paths; this is not a claim
that sprites dominate the entire emulator.

## Candidate and correctness checks

Attached sprites OR a two-bit pair mask into a byte buffer. The candidate uses
the buffer's existing 32-bit union view for aligned offsets, applying four
identical byte masks at once. Unaligned offsets retain the original byte loop.
The rounded eight-byte extent, entry metadata, pixel recording, clipping, DMA
and emulated cycle schedule remain unchanged. This is scalar ARM word batching,
not NEON or direct DMA.

- 200,000 native comparisons passed under address/undefined-behaviour sanitizers;
  49,726 exercised the aligned path. Cases include initial masks, offsets,
  widths and surrounding guards.
- Four ARM CPU/memory/beam/colour-write comparisons passed.
- PAL and NTSC attached-sprite fixtures each exercised 512 eligible recorder
  calls, with matching CPU state, RAM, framebuffer and frame hashes.

These fixtures establish their tested behaviour, not performance or universal
game compatibility.

## Physical comparison

Both runs used the same 6,000-frame scripted Banshee sequence, A1200 interpreter,
PAL native fullscreen and Paula audio. Identical private host headers suppressed
external gameplay input; the installed player's input handling was not changed.

| Build | Whole-run emulated FPS | Audio late-submit gaps |
|---|---:|---:|
| Current pixel-loop reference | 36.957 | 2,062 |
| Aligned attachment-word candidate | 36.556 | 2,093 |

The candidate is **1.08% slower** in this pair. This is enough to reject promotion,
but a single pair does not establish the exact cause or a universal regression.
Fewer source-level byte operations do not guarantee a faster compiled path.

Both runs matched dispatch count 116,472,634, cycle count 814,003,022, PC
`00029056`, and framebuffer SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
All 3,330,048 PCM sample frames were queued, submitted and completed with device
error zero. Audio gaps remain; completed delivery does not establish audible
quality. Register/MMU/cache-witness restoration and memory release passed.

## Test corrections

The first diagnostic received 518 external input events. It completed cleanly
but followed a different guest trajectory, so it is excluded from matched
comparisons. The clean repeat and measured pair suppress forwarded gameplay
events only in private test hosts. Scripted inputs and OS exit handling remain
available.

The older synthetic sprite fixture used an eight-byte pointer-register stride
instead of four. It exercised even-numbered sprites rather than all eight.
The corrected fixture uses a four-byte stride and attachment on all pairs.
Historical tests retain their narrower coverage; they must not be described as
eight-sprite tests. This was a test-fixture error, not an emulator fix.

## Outcome

Four physical runs completed: one excluded diagnostic, its clean repeat, and
the reference/candidate pair, totalling 24,000 guest frames. Temporary players
were removed, Core1 is free, and installed normal/FPU hashes were verified
unchanged. No release or firmware change follows from this experiment.

The combined recorder experiments do not support more small sprite-loop changes
as a solution to the PCM production deficit. The next investigation should
return to event/bitplane span processing, with guest-visible boundaries preserved
and matched uninstrumented measurements.

[Source changes, test generators, build hashes and logs](sprite-decisions/).
[Earlier recorder comparison](SPRITE-WIDER.md).
