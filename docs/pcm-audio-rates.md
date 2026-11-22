# PCM rate selection

The launcher offers 22 kHz PCM (default), 27 kHz PCM, and Original PCM rate.
Paula/AHI remains an independent output choice. The player receives `RATE 22050`, `RATE 27000`, or `RATE 0`; the actual source rate is published to the
ARM through `UA_RATE`. Paula's selected hardware period also determines the
producer rate, avoiding a pitch mismatch. AHI receives the selected PCM stream
rate and may mix at its configured hardware rate.

Guest Paula DMA, periods and interrupts are unchanged. This is not compressed
audio, reduced guest CPU speed, or a new Core0 offload path.

Native tests cover PAL/NTSC period rounding, invalid choices, launcher command
construction and settings round trips. Physical A500 diagnostic runs completed
300 frames at each rate with all submitted PCM delivered, zero device errors,
and clean register/cache/memory teardown:

| Choice | PAL host output | Submitted/completed stereo samples |
| --- | ---: | ---: |
| 22 kHz | 22,030 Hz | 131,072 / 131,072 |
| 27 kHz | 27,075 Hz | 161,792 / 161,792 |
| Original | 27,710 Hz | 165,888 / 165,888 |

These are transport checks, not listening tests or a measured game speedup.
Normal, 68020/JIT, FPU and experimental Cyclone hosts were rebuilt with their
recorded ARM payloads unchanged. Only the normal A500 host was exercised in
these rate checks; existing experimental-core limitations still apply.

Run `python3 scripts/test_pcm_rate.py` for the portable rate-policy test.

PCM block sizes are unchanged. Lower source rates therefore increase the time
held by each buffered block; listening and latency checks remain necessary.
