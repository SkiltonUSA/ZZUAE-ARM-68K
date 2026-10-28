ZZUAE 0.5.6-dev - Development Beta
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
Fast RAM boards. Compatible 68000 needs 32 MiB available ZZ9000 RAM;
experimental 68020/JIT/FPU needs 64 MiB, plus OS headroom.
Also required: XX19c/XACP and a supported 32-bit RTG Workbench. TF4060 is not required.
AHI v4+ with configured unit 0 is checked; without it select Paula direct or
Sound Off. lowlevel.library v40 is optional for a physical joystick.
Missing dependencies are reported, not downloaded or replaced.

Place your own media in ROMs and Disks. The default names are:
ROMs/Kick12.rom, Kick13.rom, Kick204.rom, Kick205.rom
Disks/Workbench12.adf, Workbench13.adf, Workbench20.adf
Other filenames can be selected with Browse. No ROMs or disks are included.

Open ZZUAE. Select a matching machine, ROM and disk, then Start.
RTC On uses AmigaOS time at launch; guest time advances independently of FPS.
The host clock is never changed. Guest clock adjustments are not persistent.
Optional DF1 holds a second 880 KiB ADF; Browse/Eject before Start.
Window DF0/DF1 red lights flash independently during reads; green means running.
Window Amiga+Esc toggles mouse capture; plain Esc/F8/F10 reach the guest.
Test-only F5 screenshot / fullscreen F9 ZZScanlines / Amiga+F10 exit.
ZZScanlines: Off / Classic / Soft / Gradient. Fullscreen only; off on exit.
Requires compatible FPGA firmware. No software scanlines in windows.
The Workbench game window uses 4:3 proportions and fits smaller screens.
Use ZZUAE -test for bounded runs, capture,
FPS overlay and the decorative border. Disk swapping and persistent writes
remain unfinished; demanding demos can still experience audio queue gaps.

ZZUAE-JIT provides experimental 68020 JIT/interpreter modes with a 32 MiB
translation cache. Event-bounded register groups, batched exception setup and
earlier display skipping reduce overhead. The compatible 68000 remains the default.
Optional ZZUAE-FPU adds FPU: 68882 (experimental) to either 68020 mode.
Select the accelerated CPU first, then the FPU option. Default: Off.
FPU calculations use ARM VFP double precision, not full 68882 extended
precision. Software must issue FPU instructions to benefit.

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

Periodic pauses: large amounts of temporary data on RAM: can make background
RAM-disk usage queries delay display and audio servicing. Remove only your known
obsolete temporary files after saving anything needed. Do not clear RAM: or its
ENV, T and Clipboards drawers indiscriminately. This installer does not delete
RAM contents. See the RAM-disk stall report in the source documentation.

Source, credits and updates: https://github.com/SkiltonUSA/ZZUAE-ARM-68K
