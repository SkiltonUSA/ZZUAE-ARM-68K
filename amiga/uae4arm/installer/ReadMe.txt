ZZUAE 0.5.0-dev - Development Beta
Amiga OCS/ECS Emulation on ZZ9000

Extract the installer LHA, open ZZUAE-Install and double-click Install.
Choose a parent drawer; the installer adds its ZZUAE drawer there.
Shell alternative, from the installer drawer:
  Execute Install DEST "Work:Emulators/ZZUAE"

Requires C:lha; double-click installation also requires C:IconX.
No Internet connection or existing AmiPkg installation is needed.
Close ZZUAE and any other Core1 application before installation.

Required: AmigaOS 3.x, 68020-compatible host, MUI 3.8+, graphics.library v39+,
asl.library v38+, keymap.library v37+, Picasso96API v2+, ZZ9000 graphics and
Fast RAM boards. The player needs 32 MiB available ZZ9000 RAM plus OS headroom,
XX19c/XACP and a supported 32-bit RTG Workbench. TF4060 is not required.
AHI v4+ with configured unit 0 is checked; without it select Paula direct or
Sound Off. lowlevel.library v40 is optional for a physical joystick.
Missing dependencies are reported, not downloaded or replaced.

Place your own media in ROMs and Disks. The default names are:
ROMs/Kick12.rom, Kick13.rom, Kick204.rom, Kick205.rom
Disks/Workbench12.adf, Workbench13.adf, Workbench20.adf
Other filenames can be selected with Browse. No ROMs or disks are included.

Open ZZUAE. Select a matching machine, ROM and disk, then Start.
F5 screenshot / F9 software scanlines / F10 exit.
Runs are currently bounded to 500, 1000, 1800 or 3000 guest frames.
Fullscreen, unlimited play, disk swapping and persistent writes are unfinished.
Audio queue gaps remain under investigation; A600 hardware boot is pending.

Xanxi's ZZScanlines tools are included. Install-Scanlines checks SYS:Utilities
and C: and adds only missing tools. Compatible firmware/low-resolution display
is required. No firmware, startup sequence or screen mode is changed.

Rerun Install to update. Existing ZZUAE.cfg, ROMs, Disks and Screenshots stay.
The private PackageManager drawer contains AmiPkg, its verified cache and
receipts. ZZPKG: and ZZEMUDEST: are temporary assigns. Use Install for updates;
the offline placeholder repository is not an Internet update service.
AmiPkg does not provide complete transactional rollback: back up before upgrade.
PackageManager/amipkg doctor verifies installed program files.

Manual ZIP: extract ZZUAE to a writable drawer, add your media and open ZZUAE.
Run Install-Scanlines once to add missing system scanline tools.

Source, credits and updates: https://github.com/SkiltonUSA/ZZUAE-ARM-68K
