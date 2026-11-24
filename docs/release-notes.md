# ZZUAE 0.6.2 Beta

Application/launcher and updated FPU player: **0.6.2-dev**. AmiPkg: **0.6.2-dev**.

- The optional FPU player now uses calibrated timing at stock 666.7 MHz and 800 MHz.
- A VFP-state restoration mismatch fails the run explicitly.
- Interpreter remains the default. FPU and JIT remain experimental; no new FPS gain is claimed.
- Normal, JIT and Cyclone players retain their recorded builds. Cyclone retains its stock-clock restriction.

Choose a writable destination in Install. Close emulators before updating.
Existing settings and saves are preserved. MUI and Picasso96 are required;
AHI is optional for Paula output. The optional clock service controls the whole
board; this installer neither installs firmware nor changes the clock.

The full FPU player passed PAL/NTSC boots, Banshee gameplay, audio delivery and
clean exits at 800 MHz. Stock timing passed instruction-model tests. Heavy-game
audio gaps remain, and the FPU backend does not provide full 80-bit accuracy.
[Validation and limits](validation/fpu-clock/README.md).

Every installer and component LHA includes readme.txt from the main README,
about.txt, licence.txt and the component licence notices.
