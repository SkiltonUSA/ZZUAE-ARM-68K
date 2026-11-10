# Special-service flag distribution

The earlier CPU profile attributed 15.62% of sampled dispatch time to special
service. That category includes interrupt and blitter work, not just flag checks.
This investigation determines which service requests actually occur.

## Candidate and model checks

A private candidate returns early when `regs.spcflags` equals
`SPCFLAG_END_COMPILE` exactly, clearing that flag as the original function does.
Every combined or different flag value retains the original path. Four actual
ARM differential fixtures cover memory, interrupts, beam reads and Copper colour
writes, including nonempty PCM. CPU state, RAM and output match. Direct ARM calls
with cycle arguments -1, 0, 4 and 100000 verify that the isolated flag is cleared
and other register state is preserved in both implementations.

Source inspection shows that this flag is set during exception handling. Correct
behaviour alone does not show that its isolated case is frequent enough to help.
The candidate was therefore not deployed for a hardware speed comparison.

## Physical counter run

A separate diagnostic retains the original service code and counts entry flags
for every service call at emulated frame 3000 onward. Categories are mutually
exclusive. It runs the standard 6000-frame PAL Banshee sequence with interpreter,
Paula audio, fullscreen and locked scripted input.

| Entry flags | Calls |
|---|---:|
| All calls | 18,713,281 |
| END_COMPILE only | 4 |
| BLTNASTY only | 15,561,836 |
| COPPER only | 3,098,259 |
| INT or DOINT only | 27,395 |
| Other or combined flags | 25,787 |

The isolated end-compilation case is negligible in this workload. Blitter-only
requests account for approximately 83.16% of entries, Copper-only 16.56%.
**Call frequency is not time share.** A Copper call may return quickly; blitter
service may advance chipset events. These counts do not prove that blitter
arithmetic itself consumes 83% of CPU time.

The counter build completes all 6000 frames with reference guest execution and
final pixels. All 3,330,048 queued PCM frames are submitted and completed, device
error 0; 2065 audio gaps remain. Register/cache-witness restoration and memory
release pass. Instrumented elapsed time is not an optimisation result.

## Decision

Do not promote the early-return candidate: it addresses only four calls in the
measured gameplay period. Keep the installed players unchanged.
The temporary counter player was removed, Core1 is free, and installed normal,
A1200 and FPU player hashes were verified unchanged.

The next bounded investigation is `blitnasty()` and its cycle-accounting loop,
separating that loop from the chipset events serviced by `x_do_cycles`. Any
replacement must preserve the counted free bus slots, blitter completion, Copper
service and interrupt ordering. Do not skip emulated stalls or enable immediate
blits merely to improve the reported frame rate.

[Evidence](special-service/) records both private builds, patches, model checks,
physical counters and cleanup. No ROM or game media is included.
