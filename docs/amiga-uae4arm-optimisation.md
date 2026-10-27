# ZZUAE 0.5.2-dev optimisation

The first optimisation pass targets interpreter dispatch overhead and direct
Workbench presentation. It retains the pinned UAE4ARM compatible 68000 core,
PAL chipset timing, integer-only ARM context and XACP Core1 ownership model.
No JIT, NEON, firmware change or guest CPU overclock is introduced.

## Changes

1. **Batched exception context.** The original boot loop called a protected
   single-instruction wrapper repeatedly. The new wrapper saves its integer
   exception context once per batch of up to 256 instructions. Each instruction
   still executes the original prefetch, cycle adjustment and special-event
   handling. A fault restores the outer context, invokes the existing bus-error
   handler and resumes the remaining batch unless halted. Stop polling remains
   at the same instruction interval; frame and halt bounds are checked after
   every instruction. In-progress fault accounting uses volatile storage so it
   survives `longjmp` correctly.
2. **Cached converted rows.** Scaling a 256-row source to a 480-row window repeats
   source rows. Convert each required source row once into a 2.5 KiB private ARM
   buffer, then write it to each corresponding destination row. There are no
   reads back from the uncached display bitmap and no cross-frame row cache.
3. **Specialised pixel loops.** Choose native byte order, brightness processing
   and horizontal mapping outside the pixel loop. At 640 pixels, source reads
   are sequential. Full-brightness rows skip dimming; black rows skip conversion.
   Both P96 byte orders, smaller windows and all software scanline modes retain
   the original byte-exact output, including its alpha-byte behaviour.

The display change does not reduce the number of pixels written to the bitmap.
It reduces conversion work. The bitmap remains P96-allocated and locked, with
nonce checks, bounded temporary mappings, grant/ACK ordering, blit completion
and reset-before-free teardown preserved.

## Measurement method

Physical A4000TX/ZZ9000, existing 1920×800 Workbench, 640×480 client window.
Alien Syndrome ADF, A1000 expanded 512 KiB Chip RAM, Kickstart 1.2, temporary
in-memory floppy writes, 1,800 guest frames, Direct rendering, scanlines Off.
Uncapped runs use audio Off and FPS MAX. FinalWriter remains open and idle.
No screenshots or injected input occur during measured runs. Public bridge
inspection, if any, is recorded separately from the runs it affects.

Use host BOOT elapsed time for end-to-end guest-sequence throughput; LIVE timing
also includes window startup. These are startup/title workloads, not verified
interactive gameplay rates. Audio-paced runs are measured separately.

| Build | Run 1 | Run 2 | Mean throughput | Change |
|---|---:|---:|---:|---:|
| 0.5.1-dev baseline | 61.696 s | 61.732 s | 29.17 FPS | — |
| CPU batching only | 59.505 s | 59.532 s | 30.24 FPS | +3.69% |
| 0.5.2-dev CPU + display | 40.061 s | 39.961 s | 44.99 FPS | +54.24% |

The final build takes **35.17% less time** for this sequence. Throughput gain and
elapsed-time reduction are different percentages; the two optimisations' gains
must not be added. Every run executed 8,440,230 guest instructions and 106,255,092
reported cycles, ending at PC `00fc0cd0` with frame hash `73022f00`. Every run
returned success, restored registers/MMU/cache witnesses and released owned RAM.

Most of the end-to-end gain came from presentation. The host-observed conversion/
handoff wait fell from approximately 33.49 s to 11.66 s across 1,800 frames;
P96 blitting remained approximately 11.1 s. That wait includes host polling and
synchronisation, so it is **not** an isolated ARM pixel-kernel timing.

A matched AHI run (25 displayed FPS, 1,800 guest / 900 displayed frames) improved
from **46.854 s to 36.330 s**, approaching the sequence's 36 s PAL duration.
Both delivered 1,153,024 stereo PCM frames with zero device errors. The queue-gap
counter fell from 658 to 24. This early startup sequence produced silent PCM;
these counts establish transport behaviour, not audible quality. A gap counter
measures late queue observations, not their duration. A separate 3,000-frame music/title run with Soft scanlines completed in 63.272 s,
delivering all 1,922,048 stereo frames, including 201,057 nonzero frames, with
zero device errors and clean teardown. It recorded 339 queue-gap observations.
This is not a matched scanline-Off comparison; uninterrupted audible playback
remains unverified, and the longer sequence still falls behind PAL real time.

The first CPU-only timing run had an early read-only bridge log/port inspection;
its uninterrupted repeat agreed within 0.05%. Baseline and combined runs had no
mid-run screenshots, input injection or bridge polling.

## Validation

- Native ASan/UBSan CPU-wrapper comparisons: instruction/event traces and cycle
  counts, injected opcode/special-event faults, nested double faults, halt,
  frame bounds and instruction bounds.
- Native ASan/UBSan pixel comparisons against the original scalar converter:
  the RGB565 colour space, all 81 supported widths, both byte orders and each
  brightness level used by the scanline patterns.
- ARM instruction-model baseline/candidate comparison: guest register/CCR
  prefix, Chip RAM, frame pixels, instruction/cycle counts and final PC.
  Synthetic OCS, synthetic stereo Paula DMA and real Kickstart startup cases.
  Host timestamps and native address-bearing fields are excluded.
- ARM direct-display checks: actual conversion at 640×480, 552×414 and 320×240,
  padded-row guards, source snapshots, invalid dimensions, nonce rejection,
  mapping collision, cancellation and mapping removal; delayed grant/ACK and
  ordered input checks.
- Framework `make test-amiga-arm test-amiga`; integer-only instruction audit.

Model checks do not establish physical timing, audible quality or game
compatibility. Physical logs and their build manifests remain the evidence for
performance and teardown outcomes, retained under
`amiga/records/2026-10-26/uae4arm/optimisation/`.

The Paula/Hard-scanline cancellation run reported `user_exit=1`, `failed=0`,
zero audio device errors, complete delivery of 681,984 queued PCM frames and
successful register/MMU/cache restoration and memory release.

## Installation

The matched 0.5.2-dev player and launcher are installed locally in
`SD032G:Emulator/ZZUAE`. The prior executables remain in `Rollback-051-opt`.
A 300-frame smoke run from the installed player completed with clean teardown.
Saved configuration, source media, firmware and Workbench display mode are
unchanged. The 0.5.2 development Beta packages this measured player with the updated
launcher and scanline controls.

## Repeat the local checks

```sh
clang++ -std=c++11 -O2 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -Iamiga/uae4arm tests/amiga/uae4arm/cpu_batch.cpp -o .context/test-uae-batch
.context/test-uae-batch
clang++ -std=c++11 -O2 -Wall -Wextra -Werror -fsanitize=address,undefined \
  -Iamiga/uae4arm tests/amiga/uae4arm/convert_row.cpp -o .context/test-uae-pixels
.context/test-uae-pixels
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/check_machine.py \
  2 --profile 1 --synthetic-rom --direct-live --direct-test
make test-amiga-arm test-amiga
```

`check_machine.py` also accepts `--elf PATH` and `--state-report PATH` to compare
saved and candidate ARM builds. Use matching frame/profile/audio arguments and
compare the resulting JSON files. Private media required by the fixture stays
local; synthetic ROM tests do not redistribute Kickstart or game images.
