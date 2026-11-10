# Scroll-delay plan cache

Copperline inspired exact dependency memoization; independently written C++ for
our ARM32 build. UAE already caches DMA cycle diagrams, so do not replace those.
Cache only the pure scroll-delay derivation, retaining all callers, Denise
updates, Copper timing and active DMA.

Incomplete cache (omitted resolution) fails native comparison. Full key passes
11,700,000 sanitizer comparisons including every BPLCON1 value, repeat hits and
each dependency changed alone. Build private, compare ARM mixed-mode/Copper,
PAL/NTSC and audio before hardware. No installed code changes.
