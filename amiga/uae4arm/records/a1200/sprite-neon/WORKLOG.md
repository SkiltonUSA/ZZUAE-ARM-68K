# NEON sprite compositing experiment

- Previous scalar recorder, attachment and idle-slot rewrites supplied no useful
  general gain. Test vector pixel compositing as a separate approach.
- Keep DMA scheduling, collisions and clipped/masked spans on existing paths.
- Write an actual-ARM kernel test first; the return-only stub fails output
  comparison as expected. Implement integer NEON OR compositing for 16 pixels
  and 1x/2x/4x horizontal expansion, preserving all touched SIMD registers.
- 10,560 ARM instruction-model cases pass output, guard, alignment and register
  checks. A separate 500,000-case sanitized selection/fallback test passes.
- Build from the unchanged pixel4 reference. Add the leaf to the private build's
  SIMD audit allow-list only; production scripts and installed binaries unchanged.
- Private diagnostic stage 0 calls records eligible NEON spans; its ticks remain
  zero. This counter is not a timer or a performance measurement.
- Compare PAL/NTSC sprites, unavailable-NEON fallback and core fixtures before
  a matched, bounded hardware comparison using the same input/audio settings.
