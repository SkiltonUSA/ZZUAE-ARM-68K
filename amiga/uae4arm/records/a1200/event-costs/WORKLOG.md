# Event callback profiling

- Review earlier dispatch, scanline, bitplane and special-service results. Avoid retrying rejected inlining or interpreting call counts as time shares.
- Separate the seven primary scheduled callback families from events_schedule. Sample approximately 1/64 calls after guest frame 3000. All eight 16-byte slots fit the existing profile region, ending before the JIT report at 0x482980. No new runtime allocation or guest timing change.
- Keep profiling private. Preserve the original zero-cycle service call and every production optimisation/default in the pixel4 reference.
- Prepare fine-pixel/Copper model comparisons plus a positive control that forces scheduler calls after the warm-up boundary. Keep Core1 runs serialized and installed binaries unchanged pending evidence.

- Primary profile model pixel/Copper pairs match. Actual ARM positive control records15 post-warmup scheduler samples. Physical Banshee6000 completes with reference guest state/pixels, all PCM and clean teardown.
- Primary estimates: scanline50.260s, audio5.401s, blitter2.578s, scheduler1.006s, CIA0.0203s, misc0.0032s. No scheduled Copper/DMA samples; direct/nested paths are outside those separate callback scopes. These are inclusive instrumented estimates, not additive proportions or speed gains.
- Prepare separate line-phase instrumentation to distinguish completion, Copper catch-up, decisions, drawing, device servicing and next-line setup. Its timers do not coexist with the first profiler; each starts from unchanged pixel4 reference.

- Separate line-phase build passes both pixel/Copper model comparisons. Physical6000-frame run matches reference guest execution and pixels, all3330048PCM delivered,nonzero2296574,error0; gaps2157 remain. Clean restoration/release.
- Line-phase estimates: completion42.116s inclusive; nested Copper0.224s, finish decisions32.275s, record/draw2.376s, devices6.306s. Separate next-line setup7.518s and frame completion3.033s (39samples, less certain). Empty timer floor7.76ticks/sample. Do not sum nested stages or claim these as saved time.
- No production algorithm change justified yet. Prioritize separating finish_decisions work and device servicing before another candidate. Keep timing, DMA and collision behaviour intact.
- Two complete physical diagnostics /12000guestframes. Temporary players removed; Core1 free; installed normal/A1200/FPU hashes unchanged. No version or release change.
