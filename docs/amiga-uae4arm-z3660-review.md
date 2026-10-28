# Z3660-AMIX ideas for ZZUAE

Reviewed `jusii/Z3660-amix` at commit
`51038f353cbde9df76fcb73b64f54e0f933d2760` (upstream head on 27 October 2026).
The useful ideas are memory-bank design, reducing service overhead and keeping
optimisations separate from MMU/debug modes. Its firmware is not a replacement
for XACP or the ZZ9000 firmware.

| Area | Finding | ZZUAE decision |
| --- | --- | --- |
| Direct RAM | The emulator provides separate direct RAM/ROM banks and callback-based devices. Its A3000 mapping distinguishes the host base from the guest address. | Retain dynamic, allocation-owned mappings and device callbacks. The previous guarded direct-RAM test was slower; do not re-enable it without a better measured path. |
| Translation cache | The normal JIT configuration uses 32 MiB. | Already available in ZZUAE. Keep the 64 MiB runtime allocation and metadata budget; cache size alone does not solve timing. |
| Flags/registers | The inherited JIT works backwards through each block to determine needed flags and retains translated values in ARM registers. | Larger correct blocks can make this existing machinery more effective. Avoid a second hand-written register allocator or blanket assembly rewrite. |
| Interrupt servicing | The AMIX interpreter has a tunable service cadence. Its documentation reports that cadence 2/4 boot while 8 hangs bootstrap. | Do not copy a fixed polling interval. ZZUAE must respect emulated chipset deadlines and pending special conditions. |
| Guest MMU | The AMIX path uses a 68030 interpreter with PMMU; its setup explicitly disables JIT for that mode. | PMMU is a separate compatibility project, not a shortcut to a faster OCS/ECS JIT. |
| Debug reporting | The fork gates performance/debug output. | Keep instrumentation optional and distinguish diagnostics from normal play. |

The Z3660 CPU emulator works alongside the real Amiga chipset. ZZUAE also spends
ARM time on OCS/ECS, CIA, disk, Paula and display emulation. Consequently, the
upstream CPU performance claim cannot predict ZZUAE game performance.

The reviewed JIT still passes a learned block-cycle total to its generated
exits. That alone does not resolve ZZUAE's reproduced instruction/event timing
or variable-branch-cost differences. The follow-up experiment groups only fixed-cost register operations and falls
back near chipset events. It matches the interpreter on synthetic timing tests
and the tested hardware endpoints; its performance still needs comparison with
interpretation. See [event-bounded JIT results](amiga-uae4arm-jit-events.md).

No firmware or PMMU code was imported for this review. No Z3660 physical address
is used as a ZZ9000 allocation.

## Source references

- [Repository and hardware architecture](https://github.com/jusii/Z3660-amix/tree/51038f353cbde9df76fcb73b64f54e0f933d2760).
- [AMIX modes and service-cadence findings](https://github.com/jusii/Z3660-amix/blob/51038f353cbde9df76fcb73b64f54e0f933d2760/docs/AMIX.md).
- [Memory banks, host/guest mapping and JIT/MMU setup](https://github.com/jusii/Z3660-amix/blob/51038f353cbde9df76fcb73b64f54e0f933d2760/z3660-firmware/Z-TURN/vitis_ide/Z3660_emu/src/uae/uae_emulator.cpp).
- [Interpreter service cadence](https://github.com/jusii/Z3660-amix/blob/51038f353cbde9df76fcb73b64f54e0f933d2760/z3660-firmware/Z-TURN/vitis_ide/Z3660_emu/src/uae/newcpu.cpp).
- [Flag liveness, register allocation and generated block exits](https://github.com/jusii/Z3660-amix/blob/51038f353cbde9df76fcb73b64f54e0f933d2760/z3660-firmware/Z-TURN/vitis_ide/Z3660_emu/src/uae/jit/compemu_support.cpp).

## Reuse elsewhere on ZZ9000

The allocation/cache contract and separation of RAM from side-effecting devices
apply to other Core1 applications too. The measured instruction-emitter changes
are specific to the UAE JIT; they are not automatically DOSBox or SNES speedups.
Any corresponding ARM32 emitter change should keep its own differential tests,
relocation/cache checks and matched hardware measurements. Keep XACP's existing
application-owned worker and teardown model rather than importing Z3660 firmware
initialisation or its physical memory map.
