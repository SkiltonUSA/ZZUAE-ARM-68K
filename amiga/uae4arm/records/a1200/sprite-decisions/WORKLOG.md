# Sprite decision investigation

- Continue from mixed recorder-only results; installed pair remains pixel4.
- Split private sampled timings into total decisions, display preparation, candidate scan/sort, whole recording, DMA, and nested pixel recording. Sample one in 64 calls after guest frame3000. Timers are inclusive; no speed claim from an instrumented build.
- Diagnostic passes four ARM fixtures. First hardware run completes but includes518 external input events and diverges from reference; exclude from matched results. Private host now discards forwarded gameplay events while retaining OS exit handling and scripted guest inputs. Repeat diagnostic.
- Test aligned attachment-state word OR batching, preserving original byte loop for unaligned offsets. 200000 sanitized native comparisons pass,49726 aligned; no installed change.
- Clean profiler repeat matches reference CPU counters/PC/framebuffer, zero forwarded input; record phase7.79 estimatedseconds outof9.76 total decisions, pixel subloop4.18. Scan/sort0.60, preparation0.69. Instrumented inclusive estimates, not exact walltime.
- Correct synthetic sprite DMA pointer stride from8 to4bytes; earlier fixture activated even sprites only, not all8. Corrected attached-sprite program gives512 eligible recording calls and matching ARM state/pixels.
- Candidate passes four ARM fixtures; matched uninstrumented hardware pair uses identical private input suppression, installed normal/FPU unchanged.
- Matched pair: reference36.9573977 vs attachment36.5564524emulatedFPS (-1.084885%). State/framebuffer match, PCM3330048complete,error0,gaps2062/2093, cleanexit. Reject promotion; no reverse-order performance repeat justified for a slower candidate.
- Temporary players removed; installed normal/FPU hashes unchanged and Core1free. Report, README/changelog and handoff updated locally; no release or publication.
