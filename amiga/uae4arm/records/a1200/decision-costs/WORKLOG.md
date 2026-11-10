# Display-decision profiling

Separate the measured finish_decisions hotspot into display-window, line, fetch, final drain, sprites and final state recording. Keep installed builds unchanged pending an evidence-based candidate. Preserve DMA, collisions and mid-line writes.

- Private eight-stage build completed; both 16-frame ARM direct-output fixtures match.
- Physical 6,000-frame Banshee run matches guest state, final pixels and full PCM delivery; clean teardown.
- Fetch decisions 19.297 s and sprite decisions 7.861 s dominate the sampled section; final line records 0.979 s. Inclusive diagnostic estimates, not removable time.
- Follow-up isolated sprite-slot iteration candidate is recorded separately in sprite-slots; no change to installed players.
