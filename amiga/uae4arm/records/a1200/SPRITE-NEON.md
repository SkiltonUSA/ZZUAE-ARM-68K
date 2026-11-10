# NEON sprite compositing experiment

This private experiment replaces eligible per-pixel sprite OR loops with integer
NEON operations. It starts from the unchanged four-pixel AGA reference, without
the earlier sprite-recording or idle-slot candidates.

## Scope

The leaf expands sixteen packed two-bit sprite pixels, shifts them into their
sprite-number bit pair, and ORs the result into the private cached sprite buffer.
It supports one, two or four output samples per source pixel. These are internal
sprite-resolution scales, not new launcher window-size settings.

Eligibility requires available NEON, nonzero source data, no collision processing,
no downsampling mask, a supported scale and an unclipped span or border override.
All other calls retain the original scalar routine. Sprite DMA, sorting,
attachment metadata, event timing and collision behaviour are unchanged.

The vector path writes the complete sixteen-pixel span, including transparent
trailing pixels. OR with zero preserves the existing buffer values. This is
private, allocated RAM with no device-write side effects; it is not a framebuffer
DMA shortcut. A full-span clipping check bounds every access.

The assembly leaf preserves all ten D registers it touches. It does not call
out, alter SIMD access policy or perform floating-point/saturating operations.
The private build's SIMD audit permits this named leaf only; no general compiler
SIMD exception is introduced. Runtime availability follows the existing NEON
policy and is checked at hardware-frame initialization.

## Checks

- A return-only stub first failed the output test, confirming that the kernel
  test detects missing work.
- 10,560 actual ARM instruction-model cases pass, covering every sprite bit pair,
  all three scales, eight two-byte alignments, zero/sparse/full/random pixels,
  random destination pixels and surrounding guards. Callee-saved integer
  registers, all D registers, stack, FPSCR and FPEXC are preserved.
- 500,000 address/UB-sanitized comparisons match the original recorder's complete
  buffer and collision register. They cover clipping, masks, collision settings,
  borders, scales and unavailable NEON; 91,612 take the new branch. This selection
  test uses a scalar specification of the separately instruction-tested kernel.
- Compiled PAL/NTSC sprite fixtures match reference guest state, RAM, pixels and
  frame hashes, and each exercises 512 actual NEON spans.

## Physical comparison

Four 6,000-frame Banshee runs used the same locked scripted input, A1200
interpreter020, PAL, native full screen and Paula at 27,710 Hz. Order was
reference, candidate, candidate, reference. These are whole-run **emulated FPS**,
not displayed FPS or the game's own update rate.

| Run | Build | Elapsed seconds | Emulated FPS | Audio gaps |
| --- | --- | ---: | ---: | ---: |
| 1 | pixel4 | 162.421718 | 36.94087 | 2060 |
| 2 | sprite-neon | 161.883008 | 37.06380 | 2092 |
| 3 | sprite-neon | 161.852130 | 37.07087 | 2082 |
| 4 | pixel4 | 162.429158 | 36.93918 | 2065 |

The two pairs measure +0.33% and +0.36%; median throughput is 36.94003 versus
37.06734 FPS (+0.345%). This is a small, workload-specific result. It does not
justify adding a new assembly path to the installed player without wider gains.
Keep the experiment private. Audio gaps remain and did not improve.

Both candidate runs exercise 6,381,670 NEON spans. Diagnostic stage 0 **calls**
records usage; its zero tick value is not a timing measurement. All four runs
match 116,472,634 dispatches, 814,003,022 cycles, PC `00029056`, guest hash
`eef62420`, and final pixels SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
Each delivers 3,330,048 PCM sample frames (queued/submitted/completed equal),
with 2,296,574 nonzero frames, error 0 and stopped 1. Equal counts are not proof
of equal PCM contents or listening acceptance.

Register/MMU/cache-witness, SIMD, transport and owned-memory release checks pass.
Private test players were removed and the installed normal/A1200/FPU binaries
remain unchanged. No release, firmware or default change.

## Next investigation

Use the [Copperline review](COPPERLINE-REVIEW.md) to investigate invariant
planning work separately from active DMA and pixels. The earlier idle-fetch,
fetch-table and sprite-slot candidates already failed their speed gates; do not
repeat them as new work. This experiment does not establish a hardware ceiling.

Scripts, patch, assembly, checksums, individual hardware logs and measurements
are in [sprite-neon](sprite-neon/). Model/native tests support only their covered
cases, not universal sprite compatibility.
