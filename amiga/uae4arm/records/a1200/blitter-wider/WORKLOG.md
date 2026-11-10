# Wider blitter-service validation

- Resume the private Banshee candidate: only bypass a zero-cycle BLTNASTY-only service call; leave the flag pending. Installed players stay unchanged pending the wider gate.
- Build private matched 9000-frame Slam Tilt harnesses with identical additional input. Disable external gameplay input in both hosts. Retain the normal exit path.
- Four actual ARM reference/candidate comparisons pass: memory, interrupt, beam and Copper-colour/PCM state. Direct zero-cycle BLTNASTY service leaves the register block unchanged.
- Complete 6000-frame reference/candidate intro checks on the physical A4000TX. Guest state and pixels match; all queued PCM completes, device errors zero, restoration/release clean. Reference 48.9915 versus candidate 48.9351 emulated FPS (-0.115%). No gain claimed for this pacing-limited comparison. Both PCM outputs are silent at the final recorded metric; this is not listening acceptance.
- Start the extended 9000-frame pair to reach the table. Whole-run FPS includes loading/intro and is not isolated table gameplay FPS.

- Extended pair reached the same table: reference 46.6912 versus candidate 46.7040 emulated FPS (+0.0275%). Matching guest state/pixels and nonzero PCM counts; all 4,995,072 sample frames delivered. Late-submit gaps 1252 versus 1283 remain. No useful general gain established. Keep candidate private, installed build and release unchanged.
- Completed all four physical runs / 30,000 guest frames. Removed four private test executables, confirmed Core1 free and rechecked installed normal/A1200/FPU hashes.
