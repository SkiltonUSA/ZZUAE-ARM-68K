# Fetch-loop call boundaries

- Continue after per-cycle profiling and rejected local dispatch changes. Installed players remain unchanged.
- Candidate calls the existing always-inline one_fetch_cycle_0 body directly at the two update_fetch call sites, bypassing the outlined mode wrappers. update_fetch already receives constant modes0/1/2 from its wrappers. No guest logic, DMA boundary, memory layout, cache policy or source event ordering changes.
- Hypothesis: removing per-cycle function boundaries can reduce repeated register spills and global-state reloads. Cost: larger loop bodies. Need generated-code inspection, ARM equivalence and matched physical tests; no gain assumed.
- Generated AGA64 update_fetch_2 grows2232to16612bytes; old separate7436bytecyclefunction disappears. Both cycle calls are absent in disassembly. Top-level local stack grows20to28bytes; do not infer dynamic load/store reductions from this alone.
- Four ARM memory/IRQ/beam/colour-write checks pass; PAL/NTSC mixed-mode resolution/scroll/fetch fixtures and nonempty PCM match. Fresh reference6000frames36.9308649FPS. Candidate hardware run pending.
- Straight-inline hardware6000frames35.9612528FPS (-2.625479%), gaps2164vs2063; exact state/pixels/PCM and clean release. Reject promotion. No cache-miss attribution measured.
- One structural follow-up shares one cycle body between preparation and tail phases. The original bulk block remains once at first plane0 boundary. 100000 sanitized native comparisons of actual loop source with stateful callback stubs match state and full event traces (1118bulk calls,3916470per-cycle calls across both sides). This establishes loop control flow in the fixture, not full chipset emulation. ARM and hardware gates still required.

Final: shared-loop hardware 36.5517443 FPS versus 36.9308649 reference (-1.026569%). Both candidates rejected. All three 6000-frame runs match state/pixels and PCM delivery; audio starvation persists. Temporary players removed; Core1 free; installed normal/FPU MD5 unchanged. Evidence archived locally; no release or GitHub push.
