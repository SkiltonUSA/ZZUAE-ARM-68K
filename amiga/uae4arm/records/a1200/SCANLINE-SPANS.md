# A1200 scanline span investigation

The first follow-up to [audio production tracing](AUDIO-PACING.md) tests a
constant-width AGA shifter and profiles narrower chipset paths. The experiment
retains the existing interpreter, sample rate, buffers, event timing and physical
Paula output. No candidate is enabled in the installed player.

## Constant-width candidate

The current `toscr_2_2` handles AGA 64-bit fetch-mode output with a variable
`nbits` argument. The candidate calls the same inlined implementation with a
constant 16 when a complete 16-bit span is requested, retaining the original
variable-width implementation for partial spans. It does not alter DMA fetches,
shift-register state, output position or the cycle schedule.

The emitted ARM function grows from 516 to 908 bytes. The full-span branch uses
constant shifts, but the larger function still carries register-save and stack
overhead. Code generation alone is not evidence of a speedup.

### Validation

- 720,000 sanitized native comparisons match output words and all shift-register
  words, over 0–8 planes, widths 1–16, random register contents and both fine
  scroll delays 0–63.
- The initial native harness included width zero, exposing an invalid 32-bit
  shift in both copies of the original helper. Width zero is outside the tested
  output-span contract; the corrected harness covers widths 1–16 and aborts on
  sanitizer findings. No production zero-width fix is claimed.
- Actual ARM memory, IRQ, beam and colour-write fixtures match reference CPU
  state, RAM, pixels and frame hashes. A separate ten-frame audio fixture also
  matches the reference PCM.
- Both physical runs complete 6,000 frames, with matching dispatch/cycle counts,
  final PC and framebuffer. All queued PCM completes without device errors;
  Core1 register/MMU/cache restoration and owned-memory release pass.

## Matched Banshee results

| Build | Elapsed seconds | Emulated FPS | Displayed frames | Audio gap count |
|---|---:|---:|---:|---:|
| Fresh current reference | 162.39 | 36.95 | 2,377 | 2,064 |
| Constant 16-bit candidate | 163.25 | 36.75 | 2,337 | 2,062 |

Settings are PAL A1200/68020 interpreter, native fullscreen, Paula 27,710 Hz,
the same deterministic guest input and the existing audio-pressure display
policy. These are whole-run emulated FPS, not displayed or internal game FPS.
Both deliver 3,330,048 sample frames. Final RGB565 SHA256 is
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.

The candidate measures 0.53% slower in this single pair. That is not enough to
establish a general regression, but it provides no positive reason to add the
specialisation. **Do not promote it.** The almost unchanged gap count does not
establish an audible improvement.

The earlier span-extraction rewrite also failed to improve measured throughput.
The premise that another local shift/extraction substitution would give a useful
gain has now failed twice. Further changes need evidence about how much work is
performed and which state requires it, rather than another equivalent spelling
of the same shifts.

## Narrower sound-enabled profile

A third 6,000-frame run samples one in 64 calls from guest frame 3,000 onward.
Timer totals are extrapolated using the measured hardware timer frequency.

| Path | Estimated inclusive seconds in the profiled section |
|---|---:|
| Finish scanline decisions | 34.53 |
| Decide line state | 5.38 |
| Decide bitplane fetch | 23.13 |
| Finish final fetch | 0.23 |
| AGA shift/output helper | 3.87 |
| Begin plane block | 0.91 |

These are sampled, overlapping timings; do not add the rows or subtract them
as an exact cost decomposition. Nested instrumentation and code layout affect
the measurements. The profiler's whole-run 35.77 FPS is not a candidate speed
result, and the table is not a whole-run percentage breakdown.

The shifter is a relatively small part of the remaining work. Investigation
should concentrate on the fetch-decision path and its per-cycle processing,
with exact DMA/register boundaries preserved. Earlier bulk-fetch measurements
already showed that most eligible bulk spans take the fast path; do not assume
that an unchecked larger batch is safe or useful.

The profiler passed four actual ARM fixtures and the physical run retained the
same dispatch/cycle counts, final PC and framebuffer. PCM delivery completed
without reported errors, and Core1 teardown passed. Across this investigation,
three physical runs covered 18,000 guest frames. Private executables were removed
and installed normal/FPU players verified unchanged.

## Why skipping all bitplane recording is unsafe

`line_data` is consumed by the emulated playfield and sprite collision logic,
including `do_playfield_collisions`. It is not merely a display staging buffer.
Omitting its generation on frames skipped by the presenter can change guest
collision-register results. A broader skipped-frame optimisation must preserve
those hardware-visible effects and account for mid-line register changes. This
experiment does not remove those operations.

## Alternate-line rendering

Drawing only every second visible line is a possible reduced-detail mode, not
permission to skip emulated scanlines. A 256-line image would retain 128 source
lines, then repeat them or leave dark gaps. CPU/chipset events, Copper, DMA,
collision state and audio still require their normal schedule. This differs from
scanline shading applied after rendering, which preserves the source image.

The earlier audio-only diagnostic improved whole-run throughput only from
36.84 to 38.86 emulated FPS even with intermediate drawing removed. That suggests
limited headroom for dropping half the rendered lines in this workload. It does
not measure an alternate-line implementation, which has not been built or
installed. Text and fine detail would be lost.

[Evidence](scanline-spans/) records the private source patches, build hashes,
native/ARM checks and physical logs. Diagnostic build scripts require the
prepared workspace; no game or ROM media is included.
