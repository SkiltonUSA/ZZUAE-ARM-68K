# Hard disks (.hdf)

Select **A600** (ECS) or **A1200**, then **Hard disk (.hdf) → Mount…**.
Choose an unpacked RDB hard-disk image from any mounted Workbench drive,
including an SD card or USB volume. Eject DF0 and DF1 to boot from the hard disk.
Mounting takes effect on **Start**; disk changes during a session are not supported.
**Save** remembers the image path.

Use a matching A600 Kickstart 2.05 with IDE support; revision 37.350 is used in
the physical test. The normal compatible 68000 engine works with the A600.
A500/Kickstart 1.3 hard-disk controller emulation is not implemented; the mount
control is disabled for A1000, A500 and A500 Plus.

## Images and saves

- RDB hard disks with 512-byte sectors, smaller than 2 GiB.
- The launcher checks size, sector alignment, the RDB header and its checksum
  before starting Core1. This does not prove that the guest filesystem is healthy.
- Partition-only HDF and ZIP/XZ archives are not supported. A compatible raw
  RDB `.img` can also be selected. Physical USB SD access is experimental; see below.
- **Read only** leaves guest writes disabled. **Temporary writes** applies only
  to floppies; HDFs remain read-only in that mode.
- **Save to image** writes changed blocks using the existing undo journal. It
  does not copy or validate the entire image at exit.
- Keep the image and journal sidecars together. Do not mount the same image
  in Workbench or another emulator while ZZUAE uses it. Close ZZUAE before
  removing the card. The image directory must permit session-marker creation.

## AmigaVision

[AmigaVision's documentation](https://amiga.vision/docs#optional-setups) separates
its main game collection from the optional **Amiga 500HD** and **Amiga 600HD**
Workbench setups. Those optional images are for older productivity environments;
they are not equivalent to the main collection.

The supplied `amigavision-amiga.zip` contains
`AmigaVision-Amiga-2026.04.26.img.xz`: an approximately 9.6 GiB RDB disk after
extraction, with two PFS partitions. It exceeds the file backend's size limit.
Its Workbench desktop has booted through the experimental physical USB SD backend.
Renaming it `.hdf` does not change its requirements.
The emulator archive's main HDF is similarly large. Main AmigaVision also needs
a guest configuration beyond the stock A600 profile; do not treat OCS game
support within that collection as proof that the whole installation is A600-compatible.

Select a compatible A600HD image below 2 GiB for this path. External Kickstart
and Workbench content is not included in the repository.

## Validation

Native sanitizer checks cover valid/relocated RDB headers, invalid checksums,
non-sector-aligned/oversize images, missing files and launcher command generation.
Existing storage tests cover journalled changed-block writes, interrupted-write
recovery and bounds. Physical A600 tests booted Workbench 2.0, verified a guest-created
file and confirmed a read-only reboot left the image unchanged.
[Results and screenshots](records/a600-hdf/README.md).

## Physical USB SD — experimental development build

For an Amiga-formatted SD card containing an RDB hard disk, choose **A600**,
**68000 compatible** (or **68020 interpreter**, with FPU off), then **USB SD** beside Mount. With a single mounted
USB storage unit, the launcher detects its driver unit and checks its RDB.
The field displays `USBSD:unit`; this is a physical device, not an HDF filename.
Select **Read only** and eject DF0/DF1 before Start. Save remembers the selection.
If USB units change after reconnecting hardware, select USB SD again.

The initial implementation reads through Poseidon's `usbscsi.device` using
SCSI READ(10), with 64-bit byte offsets across the host/ARM interface. No physical
write command is implemented. It does not inherit the file backend's 2 GiB limit.
A card without an RDB or with unsupported sector size is rejected. Multiple USB
units require explicit identification rather than choosing a disk arbitrarily.
The experimental 68020/JIT/FPU players have not yet been rebuilt for USB SD.

USB detection searches the first 16 sectors for a checksummed RDB, including
images whose header is at sector 2. If inserting a card freezes Workbench,
remove it and disable automatic partition mounting for that reader’s SD LUN
in Poseidon/Trident before reinserting it. Use applies this temporarily; it
does not save the configuration. Keep other readers and LUNs unchanged.
With host automount disabled, the USB SD button cannot discover the unit from
mounted volumes; enter the independently verified `USBSD:unit` in the hard-disk
field instead. ZZUAE reads the physical disk without mounting its partitions
in Workbench. This does not provide physical-card write support.


On the 31.9 GB AmigaVision card, an independent read above 4 GiB passed. After
correcting the storage completion ordering, an A600/Kickstart 37.350 run reached
the AmigaVision Workbench desktop with Amiga and Data volumes visible. It completed
1,800 frames and 577 reads, with zero writes/storage errors and clean Core1 release.
This establishes a desktop boot, not game-collection compatibility on A600.
Do not modify the card in Workbench while it is in use.

### Read 2 Error 173

The initial build could report `Read 2 Error 173 on block 1010 + 6` despite a
successful USB read. The ARM saw the new completion sequence with the previous
512-byte result instead of the current 3,072-byte result. A combined 68060 cache
writeback exposed the lower-address acknowledgement before the result.

The host now flushes the result before publishing and flushing the acknowledgement.
This also applies to file-backed disks. A native regression test models cache-line
writeback and checks changing transfer sizes and failed transfers. The physical
test passed the failing read and reached Workbench. No SD reformat or filesystem
repair was needed.

## A600 Fast RAM and AmigaVision's menu

The A600 compatible 68000 and 68020 interpreter players offer **2 MB Chip + 2, 4 or 8 MB Fast** in the
Memory selector. The extra memory is a Zorro-II autoconfig board, available to
AmigaOS and compatible WHDLoad programs. Keep FPU off; JIT and Cyclone with
Fast RAM remain unsupported. The compatible player reserves 64 MiB of host
ZZ9000 RAM. The updated 68020 player reserves 72 MiB, retaining its 32 MiB
executable cache alongside a larger heap. This is separate from guest RAM.

The supplied AmigaVision menu reports **Couldn't open screen** on A600/ECS,
including with 8 MiB Fast RAM available. Its configuration requests an 8-bitplane
screen. Extra memory does not add AGA graphics: this menu needs the A1200/AGA
path. The main AmigaVision image is intended for A1200/A4000/CD32, rather than
the separate optional A600HD productivity setup. Physical USB support in the
A1200 player remains pending; the existing USB launcher restricts it to the
A600 compatible 68000 or 68020 interpreter. Games and guest disk writes are not established by a
successful Workbench boot.

Validation used four 1,800-frame A600/Kickstart 37.350 runs: no Fast RAM,
2 MiB, 4 MiB and 8 MiB. Kickstart's Exec memory list registered each expansion;
each run completed 235 USB reads, zero writes/errors and clean Core1 teardown.
The 8 MiB diagnostic also displayed `Avail` before launching AGS2Menu, retaining
its screen-open error for inspection. This is a memory/boot check, not a WHDLoad
game compatibility test.

## USB reads and selector audio

USB reads now wait for device completion with a separate five-second timer
deadline. The previous 20 ms polling interval stalled ARM emulation on each
read and contributed to audio starvation during AGS loading.

A matched 6,000-frame A600/PAL test (2 MiB Chip + 8 MiB Fast, Paula stereo,
50 FPS display limit) recorded 383 gaps before and 175 after, about 54% fewer.
Both delivered 3,330,048 PCM frames and completed 771 reads with no writes or
storage errors; both shut down cleanly. Runtime fell from 133.68 to 122.10
seconds. These counters cover boot and selector playback, not just steady
music. Residual gaps remain; this is not a claim of gap-free audio.

## A600 68020 USB boot

Choose **A600**, **68020 interpreter**, **FPU off** and **2 MB Chip + 8 MB Fast**.
Physical USB SD remains read-only. The updated player fixes a missing-FPU probe
exception: generated FPU handlers had already advanced the PC when the no-FPU
stub raised the exception. Restoring the instruction PC lets SetPatch recognise
and recover from its probe. This does not enable a guest FPU.

A 6,000-frame physical test reached the AGS Classic ECS selector, registered
8 MiB Fast RAM and completed 836 USB reads with no writes or storage errors.
MMU/register restoration and shutdown passed. This validates selector boot,
not every WHDLoad game. [Technical notes](records/ags-audio/A600-68020.md).

Physical USB sessions now use an eight-block host audio queue and four-block
initial prebuffer. This adds about 74 ms of initial buffering at the Paula
rate. AGS tests counted 30–36% fewer gaps on the compatible 68000 and 25% fewer
on the 68020 interpreter. Gaps remain; these are event counts rather than
listening scores. Floppy and file-HDF sessions keep their earlier buffering.
