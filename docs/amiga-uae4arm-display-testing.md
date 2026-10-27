# ZZUAE display selection and testing controls

The 0.5.4-dev launcher separates normal interactive play from diagnostic runs.

- **Output:** Window or Fullscreen. Fullscreen uses an existing 640 × 480,
  32-bit RTG mode on a temporary Intuition screen, without changing saved
  Workbench resolution. Choose before starting; live mode switching is not added.
- **Normal play:** no total-frame, instruction-count or wall-time stop. Amiga+F10,
  Stop or window close ends the session. CPU dispatch batches remain bounded.
- **Testing:** run `ZZUAE -test`, or set the icon ToolType `TEST=YES`. Only this
  mode shows Run limit, Capture only and the diagnostic CPU-copy renderer. The
  icon includes `(TEST=YES)`, disabled until its parentheses are removed.
- **Capture:** F5 and the final RAM: RGB565 file are diagnostic-only. Normal
  play forwards F5 to the guest. Startup/loading splashes show the matching keys.
- **Settings:** display mode is saved; test invocation is not. Legacy limit,
  output and renderer values cannot make a normal launch bounded or capture-only.

Fullscreen retains the existing offscreen ARM-written bitmap, ownership nonce,
map/unmap, ACK and WaitBlit handoff. It is a display option, not a new page-flip
engine or claimed speed improvement. The screen and bitmaps remain allocated
until synchronous Core1 reset. A stop request has a separate five-second response
deadline before the existing teardown handles an unresponsive worker.

## Validation

Native ASan/UBSan checks cover saved settings, Shell quoting, mode selection,
legacy test-option isolation, unsigned counter wrap and timeout/cancellation
clock wrap. Actual ARM model tests cover bounded completion, invalid options,
cancellation and an unlimited run stopped after emulation has begun. The JIT
worker additionally passes vector rejection and injected cleanup-abort tests;
240 JIT/reference comparisons pass at three allocation addresses.

The first physical fullscreen attempt could not open an Intuition screen and
returned safely with all memory released. Supplying an explicit Picasso96 screen
bitmap, as in ZZDosBox, fixed that failure. The revised bounded 180-frame test
passed. An interactive fullscreen A500/Enigma run then completed 8,037 guest
frames in 161.125 seconds before F10, past the former diagnostic limits.
The host presented 4,014 frames at the selected 25 FPS display cap. F5 reached
the guest (two input events), wrote no screenshot and left the prior final-frame
file unchanged. All register/cache/MMU restoration and memory-release checks
passed. Nine late audio-queue observations were recorded; this is not a listening
test or an audio-stability claim.

The companion UB tools only analyse the Python build adapter. C/C++/ARM changes
are checked by builds, sanitizer/model tests and hardware runs; no whole-program
coverage or mutation-score claim is made.

Windowed interactive play also passed F10 exit after 33.428 seconds, with 824
presented frames, F5 forwarded, no capture writes and clean restoration/release.
Both launcher layouts were inspected on Workbench: normal mode hides the entire
Testing box; `-test` exposes it. Matching compatible/JIT players and launcher
were installed with a rollback copy. Saved ZZUAE configuration (CRC 486861BF)
and Workbench ScreenMode preferences (CRC 9C80FBC5) remained unchanged.

The installed player also passed a 180-frame capture-only run, writing its final
RGB565 without opening a display. The updated icon verified its artwork,
position and ToolTypes on re-read, including the disabled `(TEST=YES)` entry.

[Selected test logs and action record](../amiga/records/2026-10-27/uae4arm/display-testing/).
