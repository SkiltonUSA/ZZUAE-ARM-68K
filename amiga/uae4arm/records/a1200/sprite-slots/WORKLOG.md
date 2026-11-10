# Sprite DMA slot experiment

- The display-decision hardware profile isolates line setup from sprite drawing
  and final record bookkeeping. `do_sprites` is part of line setup.
- Inspect the loop: phase 1 and 3 perform no DMA callback or mutation.
- Candidate iterates phases 0 and 2 only. Preserve all original catch-up guards,
  cycle-zero reset, ordering and final horizontal-position update.
- Compare extracted reference/candidate functions under address/UB sanitizers
  over partial intervals, vblank boundaries and paired DMA-state patterns.
- Build a private player, then compare ARM sprite/pixel fixtures before hardware.
- Hardware comparisons retain PAL interpreter, scripted input and Paula settings.
  No performance claim before matched measurements; no installed-player change.

- Native: 1,116,300 comparisons and 1,345,600 matching DMA callbacks pass.
- Actual ARM PAL/NTSC attached-sprite fixtures match CPU/RAM/frame hashes.
- Actual ARM memory, IRQ, beam and Copper-write fixtures match.
- Generated do_sprites worker shrinks from 3,372 to 3,252 bytes; code-size only, not a speed claim.
- Fresh hardware reference: 6,000 frames, 162.498608 s, 36.923393 emulated FPS; candidate follows.

- Candidate completes 6,000 frames in 163.747716 s (36.641732 emulated FPS), 0.762825% slower in this pair.
- Guest signature and pixel hash match; all 3,330,048 PCM frames delivered, gaps 2,069 reference / 2,071 candidate. Teardown clean.
- Do not promote. No useful gain established; code-size reduction is not throughput evidence.
- Cleanup removes all three private players; installed normal/A1200/FPU hashes verified unchanged and Core1 free. See decision-costs/finish.log.
