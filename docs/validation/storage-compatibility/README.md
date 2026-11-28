# Storage compatibility candidates

These are isolated development builds. Installed and published **0.6.3 Beta**
players are unchanged. Interpreter remains the default. Tests used the physical
Amiga at **800 MHz KEEP**, without a listener or hands-on controller operator.
No speed gain or listening approval is claimed.

## Writable disk changes

A guest program writes to DF1, requests SwapB, writes there, requests SwapA
again and checks its earlier contents before replacing them. It runs inside
Workbench 1.3 and uses real guest filesystem calls.

| Candidate | Host writes | Storage errors | Result |
|---|---:|---:|---|
| Compatible 68000 | 88 | 0 | Write, swap, reinsert and readback pass |
| FPU player, 68020 interpreter | 88 | 0 | Same sequence passes with FPU enabled |
| Cyclone experimental 68000 | 88 | 0 | Same sequence passes at 800 MHz |

All three runs release owned memory and restore register/MMU/cache witnesses.
The three resulting ADFs from each run were downloaded and checked: boot result
PASS, SwapA `A-final`, SwapB `B-first`, and clean filesystems. The guest storage
probe uses integer code; enabling the FPU does not make this an arithmetic test.
Paired FPU and Cyclone builds now contain the disk-change hook. Their ARM tests
pass, including Cyclone's warmed self-modifying-code byte/word patch fixture.
The rebuilt FPU candidate also passes its physical arithmetic, square-root,
rounding and extended-format storage probe: 576 guest FPU instructions,
288 data operations, 24 saves/restores and zero state mismatches. This does
not establish 80-bit arithmetic.
The new Cyclone build uses calibrated timer divisors; the public retained
Cyclone binary still has its earlier clock restriction.

These tests close writable-image coverage for this sequence. They do not
complete every game's multi-disk prompt, interrupted-write recovery scenario,
or broader FPU/Cyclone gameplay compatibility.

## Experimental PCMCIA CompactFlash

The optional adapter exposes a CF/ATA image through A600/A1200 Gayle PCMCIA
attribute/configuration and I/O space. UAE's existing ATA command engine owns
sector transfers. The adapter implements CIS discovery, configuration 1/2,
linear and PC-style I/O registers, byte latching, word transfers, card status,
interrupt routing and reset. One image attaches to **either IDE or PCMCIA**.

The normal IDE path remains the default. Native sanitizer checks cover CIS
walking, configuration, byte aliases, word access and absent/disabled cards.
Linked Cortex-A9 instruction-model tests pass real ATA two-sector reads, writes,
readback, read-only rejection and reset on A600 and A1200. The A1200 IDE
regression and ATA-completion interrupt routing to levels 2 and 6 also pass. These are not physical USB-card tests.

The physical A600 guest runs Torsten Jager's `compactflash.device` 1.32. Its
sector read/write/readback test passes, and the entire host image's MD5 matches
the expected single-sector change. The boot filesystem is clean and teardown
passes. Guest drivers are installed only in disposable test media.

The A600 and A1200 FAT filesystem tests also pass using fat95: a host-created marker
is read, `Saved.txt` is written and read back, then the resulting image is
reopened with Mac mtools after shutdown. The saved text matches, its full-image
MD5 matches the Amiga copy, and the guest boot filesystem is clean. Each run
completes 3,000 guest frames with 4 host reads, 59 writes and no storage errors.

### Candidate setup

Use the paired PCMCIA player and launcher, select A600 or A1200, the 68020
interpreter and FPU off. Choose **PCMCIA** in the hard-disk row, then select a
sector-aligned CF image smaller than 2 GiB. RDB is required for IDE images,
while the PCMCIA choice also accepts partition/FAT images. This checks the
container size, not the guest filesystem's correctness.

Install [compactflash.device](https://aminet.net/package/driver/media/cfd)
inside the guest. FAT filesystems also need fat95 and a suitable CF0 mountlist.
Choose the existing write policy; persistent writes use the existing storage
journal. Do not mount the image writable on both host and guest at once.

This is an image-backed CF adapter: no SRAM/network cards, hot insertion,
simultaneous IDE-plus-PCMCIA images, or physical USB pass-through is promised.
The candidate launcher is not installed over the released player.

## Remaining physical checks

A read-only scan of USB units 0–7 found no usable RDB card. A diagnostic
repeat after the user confirmed the card was connected shows `OpenDevice`
failing on every unit. `usbscsi.device` 4.5 is resident, but Poseidon enumerates
only the gamepad and internal LCD, not a card reader. This is a host USB
detection limitation, before guest emulation starts. No A1200 physical
SD-card pass or write is claimed. Paula/AHI listening and hands-on USB-controller
checks await an operator. Full 68882 extended-precision arithmetic remains
unimplemented; current FPU arithmetic is double-backed.

## Reproduction and evidence

Use `build_retained_cadence.py --disk-swap --pcmcia` in a fresh output folder.
Use `build_fpu_clock.py --disk-swap` and `build_uae4arm_cyclone.py --disk-swap`
for paired alternate players. Do not mix ARM payloads with older hosts.
[Guest probe sources and preparation](../../../tests/amiga/uae4arm/guest/README.md)
provide reproducible checks without distributing private ROM/Workbench inputs.
Build identities and selected logs accompany this report.

Earlier unsuccessful probes are excluded: a runtime-linked guest executable
could not start on Kickstart 1.3; an initial bare build lacked the HUNK entry
stub; and `FPU ON` was rejected before startup (`FPU 68882` is correct). An
instruction-model fixture initially ran out of test-media staging space; it
now ejects the synthetic DF0 before allocating another test image. No emulator
heap increase was used to hide that harness error.

The bridge disconnected after the completed FPU check and before the next
audio candidate launch. That audio attempt made no player launch and is not
counted as a test. The last successful hardware status showed Core1 idle,
800 MHz KEEP and 59.3°C.

Follow-up after reboot: the card enumerates as USBSD:2 and the A1200 candidate
reaches the AGS selector through read-only physical USB.
[Current results](../ags-a1200-usb/README.md).
