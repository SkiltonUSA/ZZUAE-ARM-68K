# Physical follow-up: unresolved disconnect

A bounded A600 boot was attempted using the installed ZZUAE-JIT player,
**ENGINE INTERPRETER020**, Kickstart 2.05 and a private copy of Workbench 2.0.
Settings: 120 frames, FPS MAX, expanded RAM, audio off, retained 800 MHz clock.
The installed player's MD5 reported by AmigaDOS was
`06655a2aac10dfd45088f6d0c763ee34`.

The bridge lost contact after submitting the run. Network ping also stopped
answering. No completed player log or cleanup verification was retrieved;
there is no physical pass or performance result. The subsequent ENGINE JIT
comparison was **not launched**. This does not establish a JIT-specific fault.

Before the attempt: Core1 idle, Core0 AGA inactive, clock fault zero, 59.7 C.
No firmware, clock, launcher configuration or installed binary was changed.
Further hardware tests stopped; shared bridge paused and reservation retained.
After recovery, retrieve the test log from SD032G:Dev/JITCompatibility before
retrying. Physical FPU testing also remains pending under the stock-clock gate.
