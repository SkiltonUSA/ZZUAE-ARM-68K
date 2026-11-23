# Wider sprite validation

- Read prior profiles and installed-build handoff. Keep one Core1 worker at a time and installed normal/FPU pair unchanged pending a decision.
- Run matched 6000-frame Slam Tilt/Paula comparison using existing deterministic inputs.
- Inspect previous final capture: the common input sequence reaches the intro, not the table. Do not describe this as gameplay.
- Prepare identical private 9000-frame harnesses for reference/candidate with additional mouse/Return/Space input at fixed guest frames. Raise only diagnostic bounds to 9000 frames, 400M guest instructions and 450 seconds. No production setting change.
- Both 6000-frame intro runs match state/pixels and complete audio/teardown. Reference48.9966 vs candidate48.9089 emulated FPS; small pacing-limited difference, not gameplay.
- Longer reference reaches the pinball table at9000 frames and exits cleanly, averaging46.6790 emulatedFPS. Candidate running.
- Found ambiguous private harness metric: PROGRESS counts displayed frames, not guest frames. Renamed future interval field and corrected legacy summarizers to label it displayed; only equate it to emulated intervals when every guest frame was presented. Prior Banshee sound-off reference presented all6000 frames; its interpretation is unaffected. Whole-run guest FPS always uses completed guest frames/BOOT elapsed.

- Candidate completed9000 frames,193441744us/46.5256emulatedFPS, matching guest counters/PC/finalpixels. Both reachedtable; neither is an isolatedtableFPS measurement. No general gain; keepprivate.
- Cleanup passed: four privateplayers removed, Core1free, installednormal/FPU hashes unchanged.
