# Exact scroll-delay plan cache

Inspired by [Copperline's invariant caching](COPPERLINE-REVIEW.md), this private
ARM32 C++ experiment memoizes only the pure bitplane scroll-delay calculation.
Its full key includes BPLCON1, fetch size/mask, start mask, horizontal start and
Denise resolution. Hits restore both delay outputs. All DMA, Copper/Denise updates,
caller sequencing and partial-block handling remain unchanged. UAE already has
cached DMA cycle diagrams; no new whole-line schedule is assumed.

An intentionally incomplete resolution key fails. The complete implementation
passes 11,700,000 sanitized comparisons, all BPLCON1 values, repeat hits and each
input changing alone. Compiled ARM PAL/NTSC mixed-mode, mid-line scroll/resolution,
DMA/stop boundaries, memory/IRQ/beam/colour-write and nonempty PCM tests match.

## Physical comparison

Same Banshee script, 6000 frames each, interpreter020, PAL, full screen and Paula
27710 Hz. Candidate runs first, followed by a fresh reference.

| Build | Seconds | Whole-run emulated FPS | Audio gaps |
| --- | ---: | ---: | ---: |
| pixel4 | 162.461206 | 36.93189 | 2064 |
| scroll-cache | 166.380058 | 36.06201 | 2146 |

The candidate is **2.36% slower** in this pair. No promotion. Exact
caching is correct in these tests, but does not make this small calculation
cheaper overall. This is not a universal performance result or an A9 ceiling.

Both runs match final CPU state, guest cycles and pixels; all 3,330,048 PCM sample
frames complete. Register/MMU/cache-witness, SIMD and memory release pass. Counts
do not establish audio quality; gaps remain. Private test players removed and
installed normal/A1200/FPU hashes verified unchanged.

## Conclusion for this optimisation round

Repeated scalar dispatch/layout/cache experiments have not produced useful gains;
NEON sprite compositing adds only 0.33–0.36% in Banshee. Stop this series of local
rewrites. A larger event-driven chipset redesign would need new profiles and
compatibility coverage; these measurements do not justify promising its speedup.
Keep the measured production build and move to the reported GX4000 correctness
and audio faults. Evidence: [scroll-cache](scroll-cache/).
