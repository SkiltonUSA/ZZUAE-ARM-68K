# PJIT / Buffee: relevance to ZZUAE

Reviewed [nonarkitten/pseudo-jit](https://github.com/nonarkitten/pseudo-jit) at
`1d15db7dd9395ff64b2c54fdd33e218a895df5f4`. No PJIT source was incorporated,
compiled or executed on the ZZ9000 during this review.

PJIT is a 68K CPU translation engine for Buffee. Its
[design overview](https://github.com/nonarkitten/pseudo-jit/wiki) describes a
bare-metal, big-endian ARM environment with access to a physical 68K bus, rather
than a complete Amiga system emulator. The pinned `pjit.mk` targets Cortex-A8,
ARM instructions and a hard-float VFPv3 ABI.

Useful areas to investigate in our existing engine:

- Keeping frequently used guest registers in ARM registers: `pjit/pjit.h`
  documents a dedicated guest-to-host register mapping.
- Direct translation-cache indexing: `pjit/cache.c` splits guest addresses into
  tag/index/block fields. This suggests a bounded lookup experiment; it does
  not establish a speed improvement for our workload.
- Effective-address and opcode emission: `pjit/emit_ea.c` and `pjit/emit_ops.c`
  provide architectural reference points for reducing repeated dispatch work.

Our inference: these ideas are worth evaluating within UAE's existing CPU path.
Replacing that path outright would also require preserving emulated cycle/event
scheduling, Chip RAM and custom-register callbacks, interrupts, self-modifying
code handling, XACP-owned memory and executable-cache publication. Its ABI,
endianness and platform initialization cannot be copied unchanged into the
current little-endian, integer-context worker.

The repository's [licence](https://github.com/nonarkitten/pseudo-jit/blob/main/LICENSE.md)
is CC BY-NC-SA 4.0, and source headers also identify third-party origins. Licence
terms need clarification before importing implementation code into ZZUAE's
GPL-based distribution. This review proposes independent, measured experiments
inside the existing engine; it makes no compatibility or performance claim for
a PJIT port. No hardware clock or voltage settings from Buffee are applicable to
this work.

## rapid-arm-emu comparison

Also reviewed [vrtgs/rapid-arm-emu](https://github.com/vrtgs/rapid-arm-emu) at
`d762465dfd0579acba81a8dc944296522a61f929`. It describes an **ARMv9 guest
emulator**, not a 68K emulator or a runtime designed for Cortex-A9. Cortex-A9's
architecture is ARMv7-A; the similar names do not indicate compatibility.

The Rust workspace includes a shared execution IR, GCC JIT and Cranelift
backends, and fast versus optimised compilation choices. These are architectural
references. At this revision,
[`CodeCache::run`](https://github.com/vrtgs/rapid-arm-emu/blob/d762465dfd0579acba81a8dc944296522a61f929/rapid-arm-emu/src/armv9/jit.rs)
is still `todo!()`. It is not a ready-to-integrate guest execution engine for
our bare-metal XACP worker. No build or speed claim was made and no code was
imported. PJIT is the closer CPU-domain reference; neither repository replaces
the need to preserve UAE's chipset timing and test on the A9.
