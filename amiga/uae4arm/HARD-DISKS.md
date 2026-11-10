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
- Partition-only HDF, ZIP/XZ archives and physical-device passthrough are not
  supported. A compatible raw RDB `.img` can also be selected.
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
extraction, with two PFS partitions. It exceeds this backend's size limit and
has not been booted in ZZUAE. Renaming it `.hdf` does not change its requirements.
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
