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
