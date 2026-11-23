# Minimig-AGA and NanoMig references

Source review only: no FPGA build, firmware change or imported implementation.

| Repository | Inspected revision |
|---|---|
| [gyurco/Minimig-AGA](https://github.com/gyurco/Minimig-AGA) | `d0e6d5e0ba8fc9ed109451b5c36623cecdd7c9c7` |
| [MiSTle-Dev/NanoMig](https://github.com/MiSTle-Dev/NanoMig) | `5eea8461bf29069e691af827f77f25fea01df7c4` |

Both implement Amiga hardware in FPGA logic. NanoMig brings Minimig to several
Tang and other FPGA boards, with A500/A1000/A1200 modes, OCS/ECS/AGA, accelerated
68020 support, PAL/NTSC and writable floppy/IDE images. Its implementation is
not an ARM software core that can replace ZZUAE's interpreter or chipset code.
The FPGA executes hardware blocks concurrently; ZZUAE schedules chipset work
on the Cortex-A9. FPGA success does not establish an ARM performance gain.

## Useful references

Minimig's [bitplane DMA sequencer](https://github.com/gyurco/Minimig-AGA/blob/d0e6d5e0ba8fc9ed109451b5c36623cecdd7c9c7/rtl/minimig/agnus_bitplanedma.v)
expresses fetch-mode sequencing, delayed control-register/DMA effects and
display-fetch boundaries. Its [shifter](https://github.com/gyurco/Minimig-AGA/blob/d0e6d5e0ba8fc9ed109451b5c36623cecdd7c9c7/rtl/minimig/denise_bitplane_shifter.v)
separates wide fetched data from scrolling and output. The
[Copper state machine](https://github.com/gyurco/Minimig-AGA/blob/d0e6d5e0ba8fc9ed109451b5c36623cecdd7c9c7/rtl/minimig/agnus_copper.v)
is useful for examining WAIT/SKIP and DMA arbitration. These are independent
implementation references, not proof of original-hardware correctness; the
source itself retains timing TODOs.

NanoMig's most immediately useful item is its
[AGA test ROM source](https://github.com/MiSTle-Dev/NanoMig/blob/5eea8461bf29069e691af827f77f25fea01df7c4/sim/test_rom/aga_test.s).
It configures eight low-resolution bitplanes, colour indices spanning two
palette banks, and a default 64-bit fetch mode. Stripe patterns make missing
wide-fetch data visible. It also provides a 16-bit mode override and compensates
the wide fetch with a negative bitplane modulo. This offers a focused independent
test for ZZUAE's fetch, modulo and palette behaviour. The upstream ROM itself has not been assembled or run in ZZUAE. An original
fixture using its wide-fetch/stripe method is now implemented; see
[AGA fetch validation](AGA-FETCH-ORACLE.md).

NanoMig's [Verilator simulation](https://github.com/MiSTle-Dev/NanoMig/tree/5eea8461bf29069e691af827f77f25fea01df7c4/sim)
includes RAM, video, floppy and IDE models and a vAmiga Test Suite adapter.
The adapter compares screenshots against external reference images; its TODOs
include CPU revision and RAM configuration handling. Use relevant tests with
matching machine configuration rather than assuming full AGA coverage.

## Recommended use in ZZUAE

1. Add an independent wide-fetch/palette fixture based on the test ROM's method,
   with explicit expected stripes and pointer/modulo results.
2. Extend boundary tests for Copper WAIT/SKIP and DMA/register changes. Compare
   disagreements with hardware evidence before changing timing.
3. Use these checks to constrain future event batching and pixel-loop changes.
   Measure speed separately on the A4000TX with identical gameplay and sound.

A ZZ9000 FPGA implementation would be a separate hardware port, requiring DDR,
video, clocks, resource and existing-firmware integration work. No fit or timing
claim follows from NanoMig running on a differently organised FPGA.

The concurrent [fetch-loop experiment](FETCH-INLINE.md) predates this source
review. Its correctness fixtures were not derived from these repositories.
