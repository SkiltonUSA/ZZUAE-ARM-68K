# DF1 and independent read lights — 0.5.5 Beta

The launcher accepts a second 880 KiB ADF in **DF1**. Browse selects it; Eject
clears it; Save remembers it. Old settings files leave DF1 empty. Choose media
before Start: live disk swapping remains unfinished. Both drives use the same
read-only or temporary-write policy; original files are never written.

Window mode has three unlabelled lights, left to right: green running, red DF0, red DF1. Actual FIFO read
bursts, rather than the drive motor, advance independent ARM counters. The host
coalesces bursts into 60 ms red pulses with at least 40 ms off between pulses,
polling no more often than every 20 ms. A delayed poll can stretch a pulse.
Write activity does not light a read indicator. The 12-pixel status strip stays
outside the guest image and mouse area. No overlay is added to fullscreen.

## Memory and integration

DF1 staging is a linker-owned, 64-byte-aligned BSS array inside the existing
Exec allocation. The host derives its offset from the linked ELF and checks the
allocation bounds. No fixed board address is assumed. After the host publishes
the image, ARM invalidates only the untouched staging lines, calculates a CRC
and creates the private working disk image. Optional writes affect that working
copy only. Counters remain in the ARM-owned status cache line; host input stays
on a separate line.

The first two-disk JIT Workbench test exhausted the bounded metadata heap:
`compile_block` reported “Could not allocate block pool”. Cleanup restored the
register/cache witnesses and released memory. The compatible player completed
the same 1,800-frame run. Two-drive JIT sessions now reclaim metadata at 1 MiB
instead of 2 MiB, between dispatches. The 32 MiB code cache and 64 MiB allocation
are unchanged. This is a capacity fix, not a claimed performance gain.

## Verification and action log

- Added DF1 config/command/save-load tests, including empty and legacy settings.
- Added pulse timing, idle, independent-drive and unsigned-wrap tests.
- Exercised the transformed real FIFO reader for read/write/empty/deselected cases.
- Rebuilt compatible, JIT and FPU players and launcher.
- ARM instruction-model tests verify both read counters, DF1 startup CRC,
  separate temporary writes, untouched staged images, input, PCM and NEON state.
- Normal lifecycle checks cover success, cancellation and invalid options;
  JIT/FPU additionally cover compiler cleanup faults and rejected vectors.
- An initial test requested `disk_empty`, removed by link-time garbage collection;
  replaced it with the CRC published when the actual core opens DF1. An initial
  normal lifecycle command also requested a JIT-only cleanup hook; reran the
  applicable cases. These were test invocation errors, not production fixes.
- UB Python tools: disk-source transformation CC 2; no duplicate candidates;
  3/3 mutation sites killed. Those tools do not analyse C/C++; native sanitizers
  and execution tests cover that code separately.

Physical compatible-player run: Workbench 1.3 + Extras, 1,800 frames,
73.236830 seconds. DF1 CRC `404A5F8D` matches the source image. DF0 recorded
1,833 read bursts and 341 on/off pulses; DF1 recorded 87 bursts and 15 on/off
pulses. Full cleanup passed. This establishes disk access and independent lights,
not a broad two-drive application compatibility claim.

Earlier JIT performance measurements in [the batching report](amiga-uae4arm-jit-batch.md)
precede the DF1/light additions; they are not byte-identical release measurements.

The revised two-drive JIT run completed all 1,800 frames: DF1 CRC matched,
DF0/DF1 recorded 2,117/87 read bursts and 345/16 on/off pulses. All teardown
checks passed. A subsequent single-drive Alien Syndrome window/AHI check
completed 3,000 guest frames in 73.159534 seconds with matching final CPU/pixel
state and all 1,922,048 PCM frames delivered. Audio gaps remained (673); this
single follow-up is not a repeat of the earlier paired optimisation experiment.
The user requested removing the labels; final windows show only the three lights.

The 2 MiB A600 model initially exhausted heap in a test that opened a third
working image after booting with both drives. The backend-write test now ejects
DF0 after the boot assertions before opening its fresh test image. This preserves
the supported two-drive memory bound; production code was unchanged for that test
correction. Both staged source images remain unchanged by temporary writes.
