# EMU68AGA Bare Metal review

Inspected [futureretrofusion/EMU68AGA-Bare-Metal](https://github.com/futureretrofusion/EMU68AGA-Bare-Metal)
at `46e9381c0b480df521ca945ca0253e8d3961aa39`. Source review only: no build,
import, hardware execution or firmware change.

Unlike the Armiga Linux distribution, this repository contains a software AGA
chipset implementation. The standalone Raspberry Pi integration combines Emu68
with AGA-Storm/AGA-PiStorm. Its toolchain targets AArch64; aga_glue.c places the
JIT on core 0 and chipset loop on core 3 with locking. This is a different
execution/resource model from ZZUAE's single application-owned XACP Core1.
Emu68's generated instructions and Pi peripheral code cannot run directly on A9.

## Concrete techniques inspected

- `machine/core/src/playfield.c`, `blocks_dirty`: clears only the block prefix
  used by the preceding line, instead of the complete block array. This is an
  audit idea, not an established missing optimisation in ZZUAE. Our existing
  update_toscr_planes already limits clearing to newly enabled planes and
  out_offs; the data lifetimes differ.
- `machine/core/src/custom.c`, `cck_step`: bypasses Copper calls when disabled,
  stopped, waiting for a later line or blocked by the blitter. A cached wake
  interval handles some same-line WAITs. ZZUAE already has predict_copper, so
  compare prediction coverage and invalidation rather than adding duplicate
  idle checks. Prior idle-fetch/call-layout candidates failed our speed gate.
- `playfield.c` renders register-change segments into a cached line buffer,
  then writes the completed row into external framebuffer memory. `aga_glue.c`
  supplies three display buffers. This is relevant to avoiding uncached
  read-modify-write traffic, but ZZUAE already presents directly to ZZ9000
  buffers. Pi HVS code and display ownership cannot be copied verbatim.
- `custom.c` blocks its requested frame skip when collision processing is
  needed. Preserve guest-visible collision work when skipping presentation.
- `machine/arm/aga_sync.h` controls Pi HDMI vertical porch length to reduce
  cadence mismatch. It requires display-timing facilities not established in
  our XACP interface; no firmware/timing-register changes are proposed.

## Accuracy cautions

The code includes a delayed VERTB mechanism to accommodate a fast Emu68 CPU
rewriting Copper lists while another core processes them. This is not a generic
speed improvement or evidence that delaying ZZUAE interrupts is correct.
Keep CPU/chipset event ordering in our regression tests before borrowing ideas.

The README distinguishes a hardware-verified release from experimental RC8;
its status claims are not ZZ9000 measurements. No transferable FPS percentage
has been demonstrated. Files credit Emu68, AGA-Storm and UAE/WinUAE/E-UAE;
preserve the specific notices if any implementation is adopted.

## Priority

Finish the pending fine-pixel/Copper physical tests first. Next audit remaining
bulk buffer clears and cached-to-display row handling against profiling. Treat
an alternative chipset core as a separate compatibility project, not a quick
replacement for the existing UAE core.

Sources: [playfield](https://github.com/futureretrofusion/EMU68AGA-Bare-Metal/blob/46e9381c0b480df521ca945ca0253e8d3961aa39/machine/core/src/playfield.c),
[chipset scheduler](https://github.com/futureretrofusion/EMU68AGA-Bare-Metal/blob/46e9381c0b480df521ca945ca0253e8d3961aa39/machine/core/src/custom.c),
[ARM integration](https://github.com/futureretrofusion/EMU68AGA-Bare-Metal/blob/46e9381c0b480df521ca945ca0253e8d3961aa39/machine/arm/aga_glue.c),
[display synchronisation](https://github.com/futureretrofusion/EMU68AGA-Bare-Metal/blob/46e9381c0b480df521ca945ca0253e8d3961aa39/machine/arm/aga_sync.h).
