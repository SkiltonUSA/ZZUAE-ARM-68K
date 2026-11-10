# AGS selector audio: USB completion waiting

The USB backend polled SCSI completion with `Delay(1)`. On the test system,
that added scheduler-tick waits of about 20 ms while the ARM was waiting for
disk data and could not advance guest sound synthesis.

`usb_disk.h` now waits on the SCSI reply signal and a separate five-second
timer deadline. Both requests are drained before returning. Read-only card
access, Paula sample rate and audio buffer sizes are unchanged.

## Matched hardware test

A600, Kickstart 2.05, PAL, 2 MiB Chip + 8 MiB Fast, Paula stereo at 27,710 Hz,
windowed output with a 50 FPS display limit. Each run covers 6,000 guest frames
from boot through AGS selector playback.

| Measurement | Polling | Completion signals |
|---|---:|---:|
| Recorded audio gaps | 383 | 175 |
| Run time | 133.68 s | 122.10 s |
| PCM frames delivered | 3,330,048 | 3,330,048 |
| USB reads | 771 | 771 |
| Writes / storage errors | 0 / 0 | 0 / 0 |
| Clean shutdown | Passed | Passed |

**54.3% fewer gap events** in this pair. A gap event means the previous audio
request completed before its successor was submitted; this counter does not
measure audible gap duration. These are boot-and-selector results, not an
isolated steady-playback benchmark. Residual gaps remain. This result does not
establish an AGA-game audio improvement or a fix for the separate PFS requester.

## Validation

- Actual USB command function tested with mocked Exec completion: immediate,
  delayed, timeout, simultaneous replies, device error and short read.
- Address/undefined-behaviour sanitizer checks passed; both requests drained.
- Existing audio batching and USB RDB checks passed.
- Both physical runs restored MMU/cache/register state and released Core1 memory.

Source changes are in development version 0.6.0-dev. The 0.5.7 Beta release
packages do not contain this change.

## Follow-up: USB audio reserve

The larger reserve is selected only for physical USB disk sessions. It changes
host ring capacity from four to eight 1,024-frame blocks, the initial prebuffer
from two to four blocks, and the presentation reserve target from three to five
blocks. At 27,710 Hz the additional initial buffering is about 74 ms. No samples
are discarded or resampled. The maximum consecutive display deferrals remains
three. Floppy and file-HDF sessions retain the earlier buffering policy.

The four shared PCM slots and disk transfer buffer remain in their existing,
disjoint locations. The PCM compile-time bound now checks the disk buffer at
`0x488000`, not just the later video buffer.

| 68000 compatible run | Gaps | Displayed frames | Elapsed |
|---|---:|---:|---:|
| Completion-driven USB, original reserve | 185 | 4,072 | 122.39 s |
| Larger reserve experiment | 129 | 3,971 | 121.83 s |
| USB-only policy repeat | 119 | 4,092 | 121.85 s |

This is **30–36% fewer counted gaps** against the control. Each run delivered
3,330,048 PCM frames, completed 771 reads with zero writes/errors, reached the
same final framebuffer hash, and shut down cleanly. Residual gaps remain;
listening acceptance and broader game testing are separate. The first candidate
printed a stale two-block startup label; its compiled prebuffer was four blocks.
The final policy reports its actual prebuffer.

Native queue tests cover both capacities, ring wrap, consumer progress and exact
occupied-span copies under address/undefined-behaviour sanitizers. ARM model
tests cover backpressure, bounded display deferral, input and memory boundaries.
[Machine-readable results](reserve-results.json).

The [A600 68020 boot fix](A600-68020.md) resolves a separate missing-FPU exception
in SetPatch. Its silence-only failing run is excluded from audio results. Compare
68020 audio runs against each other, not directly with the 68000 boot sequence.

### 68020 interpreter comparison

After correcting the SetPatch probe, the original reserve counted 307 gaps;
the USB reserve counted 229 (**25.4% fewer**). Both runs delivered 3,330,048 PCM
frames, including exactly 2,033,526 nonzero frames, and completed 836 USB reads
with zero writes/errors. Elapsed display time changed from 124.03 to 123.13 s;
displayed frames changed from 4,147 to 4,081. Both reached the selector with
the same final framebuffer hash and restored/released resources cleanly.

The 68000 remains the default. A faster emulated CPU mode is not a guarantee
of better audio; boot timing and workloads differ between CPU models. No AHI
or full-game audio improvement is claimed from these Paula selector tests.
