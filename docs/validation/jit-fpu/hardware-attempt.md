# Physical follow-up and test-harness recovery

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
Further hardware tests stopped until recovery. After reconnecting, Core1 was
idle and Core0 AGA inactive. Directory inspection found just one empty truncated
file, `UAE-INTERPRETER020-1795521953.`: the script, log and completion paths
had the same first 30 characters. The harness now uses short distinct basenames
and verifies the script checksum before execution. The original attempt has no
usable emulator log; it cannot identify the cause of the network interruption.

Matching 20-frame interpreter/JIT retries completed with clean teardown and the
same framebuffer hash, cycle count and final PC. JIT translated two sites.
Physical FPU testing remains pending under its stock-clock gate. No clock change
was made; this recovery does not promote JIT as the default.


The 120-frame pair also completed with matching cycle count, framebuffer hash
and final PC. JIT translated 2,560 sites. Measured boot-section time was
1,307,305 us for the interpreter and 1,587,177 us for JIT (21.4% longer).
This single short boot sample is not a gameplay benchmark. Interpreter remains
the default. Both runs restored registers/cache witness and released memory.
Final Core1 idle, Core0 AGA inactive, clock fault zero, 60.1 C; bridge lease released.

[All four run logs](hardware-results.txt) · [Player identity and results](hardware-results.json).
The installed retained player tested here differs from the earlier offline
payloads; their identities are recorded separately. No installed binary changed.
