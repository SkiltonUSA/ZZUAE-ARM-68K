# Experimental Cyclone CPU adapter

Optional **ZZUAE-Cyclone Experimental Core** launcher engine. The existing
compatible engine remains the default. Cyclone has no 68020, FPU or instruction
prefetch emulation. The MOVEM odd-address stacked-PC issue found during the
evaluation is corrected in the generator adaptation and covered by a regression.

See [integration, build and limitations](../../../docs/amiga-uae4arm-cyclone.md).
`probe.cpp` runs the CPU-only fixture. `dispatch.inc` connects Cyclone to UAE's
memory/chipset event handling. Normal ZZUAE CPU builds do not include them.

Cyclone68000 by FinalDave and Gražvydas “notaz” Ignotas; pinned upstream revision
`fe89d4e2fb7b876ec71d7a8ce66affbbdf91104d`, using its GPLv2 option (LICENSE).
