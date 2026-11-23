# A1200 development checks — 0.6.0-dev

This is an experimental profile, not a compatibility release. The 68020
interpreter is the default for A1200; JIT remains optional.

| Check | Result |
|---|---|
| A1200 CPU timing | Actual ARM interpreter uses upstream's 14 MHz CPU/chipset ratio; earlier profiles retain their ratio |
| JIT timing fixture | Registers, condition codes, Chip RAM and pixels match the interpreter |
| Optional FPU | A1200 instruction-model arithmetic, rounding, storage and VFP restoration pass |
| PAL AGA | Physical 256-colour fixture, all 256 active lines, window and fullscreen |
| NTSC AGA | Physical 256-colour fixture, 240 active lines, window and fullscreen |
| HDF boot | Workbench 3.1 booted from an RDB HDF with DF0 ejected |
| HDF persistence | Guest-created file read back from the saved image |
| Write recovery | Native sanitizer checks cover partial blocks, readback, interruption recovery and boundaries |
| Alien Breed 3D | Two disks read; startup prompt reached; gameplay pending |
| Alfred Chicken AGA | Two disks read; trainer screen reached; gameplay pending |
| Standalone Slam Tilt demo | Publisher screen reached; gameplay pending |
| WHDLoad Slam Tilt | WHDLoad 20.1 starts; shadow-memory allocation errors remain |
| 1869 AGA | Four-disk HDF installation reaches new-game player selection |
| USB pad | HID/lowlevel routing implemented; physical mapping/input acceptance pending |

[Extended game tests and optimisation results](PERFORMANCE.md) include Banshee
gameplay, the wider loading checks, audio counters and candidate decisions.

The physical fixture runs completed Core1 register/MMU/cache restoration and
released their allocations. They do not prove sustained game FPS, complete
AGA compatibility, or audible quality.

The first CPU-clock regression failed with an unscaled cost of 2304 internal
ticks for the pinned core's nine-clock BRA.S. The corrected A1200 uses 1152
ticks, including the half-clock precision. The matching A500 profile retained
2304 ticks. This corrects emulated timing; it is not an ARM throughput gain.

The short synthetic display runs measured about 39–43 completed frames per
second in the tested window/fullscreen combinations. They were functional
checks without repeated controlled performance runs. The 50/60 FPS target
has not been established.

![Experimental A1200 launcher](launcher.png)

![Workbench 3.1 on the A1200 profile](desktop.png)

The logs and build hashes in this directory identify the checked artifacts.
ROMs, Workbench disks and game media are not included here.

[Gameplay CPU/chipset profiling](GAMEPLAY-PROFILE.md) records the subsequent
Banshee investigation and candidate comparisons.

[Rendered-output reuse](RENDER-REUSE.md) records exact repetition counts and the
conversion-cache experiment, which passed correctness but did not improve FPS.

[Drawing/compositing profile](COMPOSITING.md) measures the earlier renderer stages
and tests a four-pixel AGA palette-loop candidate.
