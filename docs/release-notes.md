# ZZUAE 0.6.3 Beta

Application/launcher and updated players: **0.6.3-dev**. AmiPkg: **0.6.3-dev**.

- Sound off at 25/30 FPS no longer slows guest execution in the normal,
  accelerated and FPU players. Display frames are selected at the chosen rate.
- PAL/NTSC timing, audio output choices and sound-on scheduling are preserved.
- Interpreter remains the default. FPU/JIT remain experimental; Cyclone retains
  its recorded build and stock-clock restriction. No new CPU/FPU speedup is claimed.

Install to a writable destination. Existing settings and saves are preserved.
MUI and Picasso96 are required; AHI is optional for Paula output. The optional
clock service is separate. Installation does not change firmware or clock speed.

[Validation](validation/cadence-integration/README.md) includes matched synthetic
runs and real-disk window/fullscreen pause/resume and clean exits at 800 MHz.
These checks do not establish subjective audio quality or full game completion.
Heavy-game audio gaps and full 80-bit FPU accuracy remain unresolved.

Every installer and component LHA includes readme.txt from the main README,
about.txt, licence.txt and the component licence notices.
