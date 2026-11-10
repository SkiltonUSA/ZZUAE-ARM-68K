# Copperline review for ZZUAE

Reviewed [CopperlineHQ/Copperline](https://github.com/CopperlineHQ/Copperline)
at commit `efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9`. Source inspection only;
no Copperline build, import or ZZ9000 execution was performed.

Copperline is a Rust Amiga emulator covering OCS/ECS/AGA, with a separate CPU
crate, chipset/bus model, rendering and headless control interfaces. The most
relevant material for ZZUAE is its treatment of stable DMA schedules and
observable timing boundaries. Its desktop feature set is not evidence of A9
performance or a ready-made XACP port.

## Concrete techniques

### Cached DMA plans

[`BitplaneSlotPlanCache` and `WideBitplaneHotLine`](https://github.com/CopperlineHQ/Copperline/blob/efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9/src/bus.rs)
keep an eight-entry cache of register-derived fetch plans. The key includes DMA
enable, relevant BPLCON0 bits, DDF start/stop, FMODE and hard-stop control. A plan
contains a 256-position occupancy mask; ordinary wide-fetch lines can answer
ownership queries with a bit test. Vertical gates remain live, and changed lines
use a dynamic fallback.

The separate [`DDF sequencer`](https://github.com/CopperlineHQ/Copperline/blob/efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9/src/bus/ddf_line.rs)
reuses an unchanged line's walked table only with no logged sequencer writes and
an equal complete state key, including carried state. It also avoids rewriting
the hot slot arrays when their identity is unchanged. This walked path is
FMODE=0; wide AGA fetching uses the separate plan described above. The source
documents remaining wide-FMODE comparator limitations, so it is not an oracle
for every unusual mid-line register sequence.

**Possible ZZUAE application:** audit repeated schedule derivation separately
from actual memory reads, shifter updates and collision work. ZZUAE already has
cycle diagrams and bulk fetching, and a simple fetch-order lookup previously
failed its speed gate. Copying a table lookup alone is not a new optimisation.
First establish which planning work repeats and how invalidation would cover
every relevant register/DMA boundary.

### Event-bounded idle intervals

[`advance_inactive_chip_bus_span`](https://github.com/CopperlineHQ/Copperline/blob/efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9/src/bus/dma_slots.rs)
advances only a proven idle interval. It rejects busy blitters, posted writes and
observable tracing/trap conditions, and limits the span at line, Copper wake,
interrupt-delay and next-fetch boundaries. Beam accounting and accumulated
audio time still advance.

The useful principle is proving an interval invariant before batching it.
ZZUAE already predicts Copper waits and schedules events; its rejected idle-fetch
experiments should not be repeated under a new name. There is no justification
here for skipping active DMA or emulated time.

### Indexed colour resolution

[`IndexedOutputCache`](https://github.com/CopperlineHQ/Copperline/blob/efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9/src/video/bitplane/output.rs)
uses eight frame-local entries keyed by palette and relevant mode/priority
controls, resolving all 256 indices once. HAM keeps its history-dependent path;
ordinary output still seeds the held colour for a later switch into HAM.
[`Tests`](https://github.com/CopperlineHQ/Copperline/blob/efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9/src/video/bitplane/output_cache_tests.rs)
compare cached and uncached output across indices and control combinations.

ZZUAE already uses palette lookup tables and the measured four-pixel loop.
Earlier profiling found little palette-copy cost. This is a useful correctness
reference, not evidence that another palette cache would improve our workload.

## Porting and tooling

The manifest connects `cpu-jit` to the `m68k` crate's Cranelift trace backend.
[Cranelift's target documentation](https://docs.rs/cranelift-codegen/latest/cranelift_codegen/isa/index.html)
does not provide an ARM32 backend for Cortex-A9. Its native JIT therefore cannot
be substituted directly for ZZUAE's ARMv7 emitter. A new backend or another
execution engine would be required.

Disabling desktop features exposes a headless core, but the project still uses
Rust standard-library facilities. Our bare-metal XACP runtime, file transport,
Amiga audio and owned-framebuffer contract require deliberate integration.
Desktop graphics libraries do not supply a ZZ9000 GPU backend.

The repository's [`zz9k` module](https://github.com/CopperlineHQ/Copperline/blob/efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9/src/zz9k.rs)
emulates a subset of a ZZ9000 SDK crypto service using a host-side WASM plugin.
It is not an XACP Core1 launcher or code running on the physical card.

Its [performance procedure](https://github.com/CopperlineHQ/Copperline/blob/efe1371dc15b2ce6bdaa134e5b9b2ff77c3e8bd9/docs/internals/jit-performance.md)
pins builds, media, clock mode and inputs, alternates repeated comparisons and
keeps functional checks alongside timings. The headless tooling is a candidate
for running our small test scenes on the Mac as an independent comparison.
Different emulators' timing models mean guest-state differences need analysis;
their FPS values would not be comparable to physical ZZ9000 results.

## Recommendation

Use Copperline as an architecture and validation reference. The next relevant
audit is invariant fetch-plan reuse versus ZZUAE's existing bulk/cycle paths,
with register-change invalidation and DMA/collision tests. Do not replace the
core, port its JIT blindly or claim a transferable speed percentage. Any source
adoption must retain its GPL-3.0-or-later notices and author acknowledgements.
