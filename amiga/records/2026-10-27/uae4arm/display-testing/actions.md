# Launcher display/testing update

- Read the session handoff and existing launcher, renderer and teardown contracts.
- Added a failing test proving normal launch was still bounded by the diagnostic frame count.
- Separate persistent fullscreen selection from invocation-only testing mode.
- Add Shell -test and Workbench TEST=YES; hide frame limit, capture-only output and test renderer otherwise.
- Make zero-frame LIVE runs interactive, retaining bounded CPU batches, cancellation and reset-before-free.
- Exercise counter wrap, saved configuration, test isolation and cancellation deadlines with native sanitizer tests.
- Limit F5/final-frame files to bounded tests; keep F5 available to the emulated application in normal play.
- Add temporary fullscreen screen ownership. The first hardware open failed cleanly; revised to supply a P96 bitmap as the working ZZDosBox path does.
- Keep Workbench preferences and the open FinalWriter document intact.
- Rebuild compatible and experimental JIT players to share the new command contract.
- UB companion tools support the Python build adapter, not C/C++/ARM: complexity-only CC8 for the unchanged instruction audit, no duplicate candidates; mutation discovery only. No runtime coverage claim.

- Verified temporary fullscreen, 8037-frame interactive run, F10, normal F5 forwarding and unchanged capture files.
- Verified windowed interactive exit and installed bounded capture-only output.
- Installed matched executables with rollback; verified unchanged saved settings.
- Inspected normal/testing MUI layouts and added disabled icon ToolType hint with read-back verification.
