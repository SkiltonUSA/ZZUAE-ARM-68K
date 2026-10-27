# ZZUAE machine profiles — 0.3.0-dev

The Machine selector uses plain model names. Selecting a machine updates the
chipset readout, the permitted memory options and its remembered ROM path.
ROM paths are saved separately for each machine. The DF0 disk selection remains
independent, so changing machine does not silently replace a selected game disk.
All profiles currently use a PAL 68000-compatible interpreter and one floppy.

| Machine | Chipset | Base RAM | Expanded RAM | Default Kickstart |
|---|---|---|---|---|
| A1000 | OCS | 256 KiB Chip | 512 KiB Chip | 1.2, version 33, 256 KiB ROM |
| A500 | OCS | 512 KiB Chip | 512 KiB Chip + 512 KiB Slow | 1.3, version 34, 256 KiB ROM |
| A500 Plus | ECS Agnus + Denise | 1 MiB Chip | 2 MiB Chip | 2.04, version 37.175, 512 KiB ROM |
| A600 | ECS Agnus + Denise | 1 MiB Chip | 2 MiB Chip | 2.05, version 37.299/300/350, 512 KiB ROM |

Start rejects a missing ROM, wrong size, invalid checksum or wrong ROM family.
The player also verifies the size/checksum/version before guest execution. The
actual Kickstart version is read from the image; it is no longer hardcoded to 33.
256 KiB ROMs are mirrored in the 512 KiB ROM window; 512 KiB ROMs occupy it fully.

The A1000 profile starts with Kickstart already loaded; it does not emulate the
initial Kickstart-disk bootstrap or write-protected control-store hardware.
Model-specific preloaded ROM, RAM and OCS compatibility are the present scope.
The core's A500/A500 Plus/A600 compatibility presets control CIA overlay and
DF0 identification behavior. A600 also has the required ROM mirrors and a small
empty-slot Gayle register implementation based on the pinned UAE4ARM source.
No IDE drive or PCMCIA card is attached; those media backends and RTC delivery
remain unimplemented. This is not full peripheral or cycle-exact compatibility.

## Shared memory

The 32 MiB Exec allocation is unchanged. The frame remains at offset 0x490000,
ROM staging moves to 0x4e0000 (capacity 512 KiB), and DF0 to 0x560000. The shared
noncacheable interval now ends at 0x640000, where private BSS begins. Compile-time
checks reject overlapping media regions. Runtime mapping/nonce checks and the
existing restoration/reset-before-free sequence remain required.

Before guest boot, every mapped Chip RAM bank is checked at its first and last
longword, detecting aliased expansion banks. The existing full Slow RAM test is
retained. These tests explicitly remove the reset ROM overlay during RAM checks.

## Media and verification

The supplied 1.1/1.2/1.3 Kickstart disks were read and their embedded payload
checksums inspected. The unmodified 33.166 image remains the A1000 default.
For A500, the existing DEVS:Kickstarts/kick34005.A500 image was read and verified
as 34.5 with a valid checksum. Modified disk variants are not the selected default.
The ROMs remain private installation media and are not distribution assets.

A clean A500 Plus Kickstart 2.04 image was subsequently supplied and staged.
Kickstart 2.05 was missing at this initial stage; 37.300 and 37.350 were
subsequently supplied. Workbench 2.0 ADFs are OS disks, not substitutes for
those ROMs. Later A600 physical results are recorded below.

The next supplied batch included a valid A3000 36.143 image; it is retained
as source media but is not assigned to A500 Plus/A600. The unmodified supplied
A500 34.5 image exactly matches the selected DEVS copy (SHA-256
`ee05862d8102a08436ac4056da7d549db31625c7d47b24dfb7b3c9a5c113ca53`).
Three supplied 1.3 `[b]` variants and the truncated 1.2 `[b]` image failed their
ROM checksums. Repeated 512 KiB copies were identified, not mistaken for native
512 KiB ROMs. No original media was rewritten.

Native settings/ROM-version tests and all nine ARM instruction-model cases
passed: both memory choices for each machine plus the legacy OCS regression.
A1000/A500 cases used actual 1.2/1.3 ROMs for a one-frame boot; ECS cases used a
small synthetic 68000 ROM, not Kickstart 2.x. The latter verify the memory banks,
ECS mask, compatibility preset, overlay mode and A600 empty-slot Gayle registers.
They do not establish real Kickstart 2.x or Workbench 2.0 boot compatibility.

The supplied clean A500 Plus 37.175 ROM and its `[!]` variant are byte-identical,
with valid checksum and SHA-256
`d0b70e8a1772614b897f92c33cb299bed3fc8e3de488fc12f67f97fc2486eb79`.
The oversized `[b]` image failed checksum validation. A known A3000 37.175 ROM
has a different CRC despite the same version; both GUI and player explicitly
reject that recognized A3000 variant, as well as the supplied A3000 1.3/2.0 images.
This identification is not a complete ROM database: unknown checksum-valid
modified images still require compatibility tests.

The clean 2.04 image passed an actual ARM one-frame boot with 2 MiB Chip RAM in
the instruction model. Physical acceptance is recorded separately below. A
private copy of the supplied Workbench 2.0 ADF uses the existing minimal
LoadWB/EndCLI startup to avoid its initial keyboard-map requester; the original
ADF remains unchanged. It is staged as Disks/Workbench20.adf, with ROMs/Kick204.rom.

## Physical checks

A1000 with preloaded 33.166 and 512 KiB Chip completed 1800 frames, with final
frame hash matching the previously verified Workbench 1.2 desktop. Memory,
MMU/register/cache restoration and allocation release passed.

A500 Plus with the supplied 37.175 ROM and 2 MiB Chip completed 1800 frames
and visibly reached the Workbench 2.0 desktop. The final capture is saved in
`.context/amiga/uae4arm/launcher/plus-workbench20.png`. Memory verification and
all restoration/release checks passed. This establishes a floppy desktop boot,
not general game/OS/peripheral compatibility.

The physical MUI machine cycle responds to keyboard Down: changing A1000 to
A500 automatically selected ROMs/Kick13.rom, 512 KiB Chip and OCS/PAL.
Further changes selected A500 Plus with Kick204/1 MiB/ECS, then A600 with
Kick205/1 MiB/ECS. Save persisted the selected A1000 profile and all four ROM
paths. At that stage the A600 path was reserved for a future matching image. It now
contains the validated 37.350 ROM, with 37.300 retained alongside it.

A500 with 34.5, 512 KiB Chip and 512 KiB Slow completed 1800 frames with the
verified Workbench 1.2 desktop hash. Memory and all restoration/release checks
passed. These bounded startup checks do not establish sustained gameplay speed.

## A600 / Workbench 2.0 hardware validation — 0.5.4 development

Both supplied Kickstart 2.05 revisions booted the supplied Workbench 2.0 disk
on the physical A4000TX/ZZ9000:

| ROM revision | Chip RAM | Guest frames | Result |
|---|---:|---:|---|
| 37.350 | 1 MiB | 1,800 | Workbench desktop reached |
| 37.300 | 2 MiB | 1,800 | Workbench desktop reached |

The disk's `Libs/version.library` reports **37.67 (16.7.91)**. These tests used
`Disks/Workbench20.adf`, the existing private LoadWB/EndCLI startup copy. They
verify that desktop boot path, not the original disk's entire Startup-Sequence.
The ROMs and original disks remain unchanged. These are two different ROM/RAM
configurations, not a controlled renderer performance comparison.

Both memory checks passed, with no SIMD-state mismatches, display failures or
register/MMU/cache restoration errors. All owned memory was released. This does
not establish IDE/PCMCIA support, unlimited execution or general A600 game
compatibility. See [the follow-up report](amiga-uae4arm-054.md).
