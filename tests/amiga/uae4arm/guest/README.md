# Guest storage checks

These programs run **inside ZZUAE**, using AmigaOS filesystem/device calls.
Use disposable media only. They are not tools for the physical host's disks.

Build with the Amiga cross compiler, putting `entry.s` first:

```sh
m68k-amigaos-gcc -std=c99 -nostdlib -noixemul -m68000 -fno-builtin \
  -Os -Wall -Wextra -Werror entry.s disk_swap.c -o SwapProbe
m68k-amigaos-gcc -std=c99 -nostdlib -noixemul -m68000 -fno-builtin \
  -Os -Wall -Wextra -Werror entry.s pcmcia.c -o CFProbe
```

The entry stub is necessary: Amiga HUNK executables enter at the first code
byte, not an ELF entry-point field. No C runtime is linked, keeping SwapProbe
usable on Kickstart 1.3 without a newer `utility.library`.

## Disk swaps

Copy SwapProbe to `C:` on a disposable Workbench boot ADF. Set its
`S/Startup-Sequence` to `Stack 32768` followed by `C:SwapProbe`.
Create two formatted OFS ADFs with volume names `SwapA` and `SwapB`; each
contains `Marker` with `A` or `B` followed by a newline.

Boot with SwapA in DF1 and persistent writes enabled. Wait for the prompt,
then use Amiga+Esc to insert SwapB and subsequently SwapA. The program closes
files and waits before each requested swap. Success requires:

- Boot disk `SwapResult.txt`: `PASS guest write, swap, reinsert, readback`
- SwapA `Saved.txt`: `A-final`
- SwapB `Saved.txt`: `B-first`
- Clean host teardown and clean filesystem checks on all three resulting ADFs.

## PCMCIA ATA

Use a disposable 8 MiB image filled with byte `0x55`, an A600/A1200 ROM,
and a Workbench 2.0+ boot ADF. Put CFProbe in `C:` and
`compactflash.device` in the guest's `Devs:`. Run CFProbe from the startup
sequence. Use the experimental player's `PCMCIA <image>` argument with
persistent writes. This check does not install a driver on the physical Amiga.

The probe refuses to write unless sector 3 contains the expected initial
pattern. It reads, writes and reads back that sector through the guest driver.
Success requires `CFResult.txt` containing
`PASS guest compactflash.device read/write/readback`, the expected bytes in
the host image, and clean teardown. This is a device check, not FAT mounting
or hot-removal acceptance.

The test driver is Torsten Jager's CFD 1.32, available from
[Aminet](https://aminet.net/driver/media/cfd.lha); its archive includes source
and licence terms. Workbench and Kickstart are external test inputs and are
not included here.

## PCMCIA FAT file transfer

Build `fat_transfer.c` with the same entry stub. Format a disposable 8 MiB
image as FAT and copy `Marker.txt` containing `ZZUAE FAT transfer test` plus
a newline into its root. Install CFD and fat95 inside a disposable Workbench
2.0+ guest boot disk, with a CF0 mountlist pointing to `compactflash.device`,
unit 0. Mount CF0 before running the probe.

The probe reads the marker, creates `Saved.txt`, reads it back and records
`FATResult.txt` on the boot disk. Verify the saved file from the host after the
player exits; do not mount the same image for writing on both sides at once.
The guest's delayed writes must finish before clean exit. This test exercises
filesystem use, separately from the raw ATA-sector probe.
