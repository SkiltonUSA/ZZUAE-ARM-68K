# ZZUAE live-window milestone

26 October 2026. Same pinned UAE4ARM core, PAL A500/68000-compatible interpreter,
512 KiB chip RAM and Kickstart 1.2 as the initial prototype. This work adds live
presentation and input transport; it does not enable JIT, NEON, host PCM audio,
fullscreen or cycle-exact CPU emulation.

## Implementation

- A Workbench window receives frames while Core1 is running. The initial
  RGB565/Picasso96 pixel-transfer implementation was too slow.
- The replacement follows ZZDosBox's direct-window design: an allocated,
  locked P96 bitmap is temporarily mapped into the ARM's private page tables.
  Nonce checks at both ends verify the translated address before any write.
- Scalar ARM code converts RGB565 into the Workbench's native 32-bit format.
  The 68K coordinates the handoff and blits the completed bitmap through
  Intuition. Frame pixels no longer make a 68K round trip in this path.
- The next CPU frame can start while the previous bitmap is blitted. A new
  bitmap grant is withheld until `WaitBlit` completes. The ARM does not write
  directly into Workbench's screen bitmap.
- A bounded input ring forwards raw keys and mouse events. Cursor keys also
  operate guest joystick port 2; left Alt is fire. Focus loss releases held
  inputs. Physical joystick hardware is not integrated into this frontend.
- F10, Ctrl-C and the close gadget request cooperative termination. P96 locks,
  the bitmap and the window survive error paths until synchronous Core1 reset.
  Cancellation now retains a final guest capture and counters.

There is a nominal 50 Hz presentation cap. The current implementation does not
maintain 50 displayed frames/s in all tested workloads, and has no automatic
frameskip. The window uses uncorrected 640 × 256 geometry; aspect correction,
resizing and fullscreen are separate pending changes.

## Physical measurements

| Run | Presented frames / host interval | Average | Result |
|---|---:|---:|---|
| Initial pixel-transfer Workbench path | 571 / 95.852 s | 5.96 FPS | F10 exit; 88.495 s in P96 pixel transfer |
| Direct bitmap Workbench path | 1800 / 39.914 s | 45.10 FPS | Requested guest frame count completed |
| Overlapped direct Workbench path | 3001 / 64.737 s | 46.36 FPS | Guest count 3000 completed; visible desktop captured |
| Bounded Alien Syndrome startup | 1801 / 39.438 s | 45.67 FPS | Guest count 1800 completed; final hash `73022f00` |
| Longer Alien Syndrome title/credit sequence | 5201 / 120.001 s | 43.34 FPS | Hit diagnostic wall-time limit; restored and released resources |

The presentation count can differ from the guest vertical-frame counter by one
because upstream drawing also flushes an initial/final frame. Rates above use
the host's `LIVE` counters and include final capture overhead. For the bounded
Alien run, the ARM request itself took 39.287081 seconds for 1800 guest frames.

These are startup/desktop/title workloads, **not verified gameplay FPS**.
Different durations, states and screenshot activity prevent treating these rows
as controlled percentage-gain comparisons. The direct path clearly removed the
large pixel-transfer bottleneck, but the overlap change needs matched repeated
measurements before attributing a precise gain to it.

Workbench visibly reached its desktop. Alien Syndrome displayed its illustrated
title and credit screens. Injected fire/Space events reached the frontend's input
ring, but title transitions may also be automatic; this is not proof that the
game accepted them. Gameplay and movement remain unverified. Badlands captures
after an injected fire press were black; that loading/input transition remains
unresolved. Do not count it as a gameplay pass.

The 120-second Alien test returned a timeout/application error, not a successful
completion. Its register/MMU/cache restoration, RET1, Core1 reset and owned-memory
release all passed. A separate latest-build F10 test stopped after 378 guest
frames, returned success and retained its capture. Other completed bounded runs
also returned success with restoration checks passing.

After the final fractional-mouse correction, a 240-guest-frame deployment smoke
test also returned success with all restoration checks passing. Core1 was left
free and Workbench/the bridge remained running.

## Verification and evidence

- ARM instruction-model tests exercise publication/grant/ACK ordering, stable
  frames while the host delays, ordered input and releases.
- Actual ARM conversion tests cover both P96 byte orders, padded rows, destination
  bounds, a failed nonce, an existing mapping, and cancellation/unmapping.
- Native checks cover input-ring counter wrap and accumulation of single-pixel
  mouse movement. Synthetic OCS output remains byte-exact.
- `make test-amiga-arm test-amiga` passed. Those framework/simulator checks do not
  replace the physical runs.

Raw evidence is under `amiga/records/2026-10-26/uae4arm/live/`; private screenshots
are in `.context/amiga/uae4arm/`, including `live-workbench-overlap.png`,
`live-alien-title.png` and `live-alien-after-fire.png`.

Only temporary RAM: executables/media were deployed. No firmware, startup,
saved display mode, native emulator installation or original supplied ADF changed.
`RAM:ZZUAELive` is the development executable; invocation and controls are in
[the prototype README](../amiga/uae4arm/README.md#live-window).

Next priorities: measured frame scheduling toward sustained PAL speed; actual
game-start/input validation; batched Paula/AHI audio; aspect-correct window and
fullscreen presentation. Broader A1000/ECS/A600 compatibility remains pending.
