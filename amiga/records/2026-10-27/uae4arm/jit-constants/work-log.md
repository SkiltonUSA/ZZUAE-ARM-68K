# MOVW/MOVT constant-loading experiment

- Continue from corrected instruction-timing reference, standalone main4ef92aa.
- Isolate only LOAD_U32; preserve other ARMV6T2 paths and literal-load baseline.
- Check emitted A32 execution, registers/flags, no literal reads, then CPU/timing regressions and matched physical Frontier runs.
- Installed application, preferences, firmware and unsaved FinalWriter document remain untouched.

- Recorded a failing literal-loader test before selecting the existing upstream MOVW/MOVT branch.
- Added --movw-constants as a separate output variant; left global ARMV6T2 disabled.
- Executed 7,830 constant/register cases at two addresses, with UBSan on the emitter harness. Values, unaffected registers and flags match; no data reads.
- Mutation testing exposed a gap in checking surrounding emitter text; added preservation coverage. All 12 mutations detected; helper CRAP 2 at 100% line coverage; no duplicate candidates >=0.8.
- Fresh baseline A1: 3,000 frames, 58.945569 s, 426273780 guest cycles, PC 00c3b724, frame hash 1566eac0. Clean teardown.
- Generated source audit: only codegen_arm.cpp LOAD_U32 and required macro definitions in codegen_arm.h differ from reference.
- Candidate CPU model: 432 cases at three relocated addresses; actual MOVW/MOVT execution observed, generated code exercised near cache end, page permissions restored.
- Candidate timing matrix: beam, variable branches, forced IRQ and metadata pressure match interpreter cycles, PC, registers/CCR, Chip RAM and pixels.
- Cancellation and injected data-abort recovery pass at all three addresses.
- Built and staged candidate CRC5F193670 in RAM only; reference CRC5770E67A retained.
- Physical A1/B1/B2/A2 elapsed seconds: 58.945569 / 58.269194 / 58.266316 / 58.950660. All 3,000 frames, cycles426273780, PC00c3b724, hash1566eac0; zero reported witness/register errors and owned memory released.
- Mean elapsed58.9481145 ->58.267755s; throughput +1.1676%, elapsed -1.1542%. Headless startup/intro only, not unique game FPS. Candidate remains an isolated option.
- Postflight: Core1 idle, FinalWriter retained, installed JIT/launcher/config and saved screenmode CRCs unchanged.
- Scoped code/tests committed to standalone as70b0ce5. No ROMs, media, preferences or unfinished sharing sources exported.
- Reclaimed only the temporary emitter-harness source copy; retained evidence and reusable builds.
