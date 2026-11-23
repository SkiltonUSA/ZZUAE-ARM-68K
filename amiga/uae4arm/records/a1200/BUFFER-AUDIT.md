# AGA buffer clear and copy audit

The EMU68AGA review suggested bounded clears and cached rendering before writing
the display buffer. ZZUAE already uses both techniques. This round measures
remaining out-of-line `memcpy` and `memset` calls without modifying the player.

## Method

`check_machine.py --buffer-report report.json` counts requested bytes and calls
at the ARM library entry points, grouped by caller and whether the first frame
has completed. It excludes compiler-inlined operations and does not measure
elapsed time, Zorro traffic or cache-maintenance cost. The phase after the first
frame also includes final diagnostic capture, so it is not purely gameplay.

Two generated PAL diagnostics run for 16 frames with the installed build's ELF:
fine pixels and mid-line Copper colour changes. Each runs with counters off/on
in both shared-copy and direct-framebuffer modes. CPU flags/registers, Chip RAM,
final pixels, PCM and result records must match within each pair. Direct-mode
comparisons also include every acknowledged framebuffer hash. The direct test
uses a 640×480 granted bitmap; it does not benchmark the physical 320×256 mode.

## Findings

Counts below cover the phase after the first frame, including final capture.

| Operation | Fine pixels | Copper colours | Interpretation |
|---|---:|---:|---|
| Shared presentation copy | 15 × 327,680 bytes | 15 × 327,680 bytes | Absent in direct mode |
| Final diagnostic capture | 1 × 327,680 bytes | 1 × 327,680 bytes | End-of-run capture, not a per-frame display copy |
| Line-state clears | 4,681 × 256 bytes | 4,681 × 256 bytes | Five clears per reset: 128 bytes and four of 32 bytes |
| Recorded palette copies | 15 × 2,052 bytes | 345 × 2,052 bytes | Copper changes require more recorded palette states |
| Drawing palette copies | 15 × 1,024 bytes | 345 × 1,024 bytes | Tracks the increased palette-state count |

The larger startup clears occur before the first frame; they are not repeated
full-buffer clears on every rendered frame. Source inspection confirms that
sprite storage is cleared only across its used span, and enabling additional
bitplanes clears only the earlier output span of those newly enabled planes.
The direct renderer converts a repeated source row once in cached scratch and
writes the granted display bitmap without reading it back.

The palette-copy increase is a useful profiling lead, not evidence that copies
can simply be removed. Earlier scanlines need their recorded colours after the
guest changes registers. Any replacement must preserve those snapshots, HAM and
mid-line changes, then pass matched physical gameplay timing tests.
`remember_ctable` already reuses an unchanged palette, and
`adjust_drawing_colors` already skips a matching table. Adding a generic dirty
flag would duplicate those existing checks. A useful experiment would need to
measure the cost of copying changed palette snapshots specifically.

No production optimisation, FPS gain, default change or new binary is claimed.
The largest apparent copy was already avoided by direct presentation. See
[evidence](buffer-audit/) and the [source review](EMU68AGA-REVIEW.md).

## Reproduce

Append `--buffer-report report.json` to a normal `check_machine.py` run. Use
`--live` for shared-copy presentation or `--direct-live` for the granted bitmap.
Use `--state-report state.json` on both counter-off/on runs and compare them.
Run these model checks serially because the harness shares a capture filename.
