# Independent AGA fetch oracle

- Read NanoMig's AGA test ROM and Minimig's bitplane DMA sequencer; retain source-only firmware scope.
- Added original generated 68000 diagnostic ROM with eight planes and all 256 palette indices. Pattern varies across columns and rows; expected RGB565 pixels are computed outside UAE.
- First local fixture had DIWHIGH HSTOP bit 8 clear, producing a 64-pixel window. Corrected the diagnostic's horizontal endpoint, not emulator code.
- First extension to 32-bit fetch assumed 40 bytes with DDFSTOP $d0. The row checker rejected it at row 1. Reviewed end-sequence behaviour and corrected fixture modulo to -4 for modes 1/2; modes 0/3 use 0/-8. Failure log preserved. Expectations were not changed to match corrupted output.
- Test runner checks every pixel of all 192 diagnostic rows for four FMODE values under PAL and NTSC, plus deliberate wrong-modulo and altered-pixel rejection controls.
- Production emulator source, player, defaults and firmware remain unchanged.

- All eight valid ARM-model cases pass. All 256 RGB565 colours occur. Checksums verified for every generated ROM. Wrong-modulo guest ROM fails at row 1; altered-pixel controls fail.

- Physical A4000TX: all eight PAL/NTSC fetch configurations pass, 120 frames each (960 total). All final captures match expected pixels and ARM-model captures. Clean register/cache restoration and memory release; no disk I/O. Temporary ROM removed; installed A1200/FPU MD5 unchanged; Core1 free.
- Added repeatable test instructions, source acknowledgements and limits to README/report; no production emulator source change, version bump or firmware work. No GitHub push this turn.
