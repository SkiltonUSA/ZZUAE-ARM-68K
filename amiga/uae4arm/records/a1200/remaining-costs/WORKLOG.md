# Remaining A1200 costs

- Read prior matched reports. Premise rejected: local bitplane shifter and idle-loop substitutions will close Banshee's PCM production gap. Multiple tested variants showed no useful gain.
- Retain the current pixel4 interpreter and all guest event schedules.
- Build sound-enabled sampled CPU-stage diagnostic from current base, then narrower scanline/sprite/collision/palette diagnostic. Establish timings before choosing another change.
- CPU diagnostic passed four actual ARM fixtures. Restarted the stopped Mac MCP server; the Amiga bridge connected normally. Started one bounded 6,000-frame Paula hardware profile.
- Fixed a private profiler insertion signature (`do_sprites(int hpos)`); rebuilt the diagnostic, no production change.
- Found disabled-plane reads in sprite/playfield collision checking. Moved eligibility before private-buffer load in a separate candidate. 200,000 sanitized comparisons match collision results; fixture reads fall from 7,032,766 to 3,669,523. This is not a whole-game gain.
- Sound-enabled dispatch profile confirms 57.11% event advancement, 21.91% opcode work, 15.62% special service, 5.36% bookkeeping; physical run passed.
- Remaining-cost profile records 8.22 estimated inclusive seconds in sprite decisions/recording, 3.27 in sprite DMA, 0.78 DIW, 0.22 palette; no collision samples. Do not promote the disabled-plane change for this workload; no hardware speed test planned for that candidate.
- Test a separately specialised unclipped, unmasked, non-collision sprite recorder, with original fallback. 500,000 sanitized buffer/clipping/collision comparisons pass (121,567 fast-path cases). Fresh reference started while candidate builds.
- Sprite candidate passed four actual ARM fixtures and PCM comparison. Added a synthetic eight-sprite DMA guest program; PAL and NTSC each hit 256 eligible calls and match CPU/RAM/pixels.
- Fresh 6000-frame reference completed cleanly: 162428278us / 36.93938 emulated FPS. Candidate hardware run follows serially.
- Reverse-order repeat confirms 0.56694% and 0.62845% Banshee gain. All results and clean exits match; audio starvation persists. Retain sprite candidate privately pending wider coverage, leave installed normal/FPU pair unchanged.
- Wrote remaining-costs report, local README/changelog and session handoff; archive code and evidence without ROM/game media. No GitHub publication/release requested this turn.
