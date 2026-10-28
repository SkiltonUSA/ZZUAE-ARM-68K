# ZZUAE installer

The development Beta offers an offline AmiPkg installer and a manual-copy ZIP.
Both contain the same launcher/player, icons and bundled Xanxi scanline tools.
Kickstart, Workbench and games are supplied separately.

Extract the installer LHA, open **ZZUAE-Install**, then double-click **Install**.
Choose a parent drawer. For an exact destination, use a Shell in that drawer:

```text
Execute Install DEST "Work:Emulators/ZZUAE"
```

Requires `C:lha` and, for double-click launch, `C:IconX`. No network connection or
preinstalled package manager is required. Close ZZUAE and other Core1 applications.

## Dependency checks

| Component | Installer behaviour |
|---|---|
| MUI 3.8+, graphics v39+, ASL v38+, keymap v37+ | Required |
| Picasso96API v2+, ZZ9000 graphics and Fast RAM boards | Required |
| AHI v4+, audio modes and unit 0 | Checked; Paula direct and Sound Off remain available |
| lowlevel.library v40 | Optional physical joystick support |
| Launcher / Core1 task | Installation stops while active |
| XACP/FPGA firmware, 32 MiB compatible / 64 MiB accelerated allocation and display format | Player runtime checks |

Missing components are reported, not downloaded or replaced. The TF4060 is a
tested configuration, not an installer requirement. AHI detection plays no sound.
The default launcher sound choice is AHI; choose Paula or Off if AHI is missing.

## Data and scanlines

Existing settings, ROMs, disks and screenshots are outside the package receipt
and preserved during upgrades. The installer creates their drawers when absent.
Xanxi's `Install-Scanlines` helper adds missing system tools and preserves existing
copies. It does not change firmware, startup files or display modes.

The private `PackageManager` drawer holds AmiPkg, cache and receipts. `ZZPKG:` and
`ZZEMUDEST:` are temporary assigns. Rerun **Install** to update; the `.invalid`
repository URL deliberately provides no online feed. `PackageManager/amipkg doctor`
checks installed program files. The upstream copy engine has no full transactional
rollback, so keep a backup before upgrading.

## Integrity and source

The installer verifies an Ed25519 catalogue signature before staging and AmiPkg
checks the payload SHA-256 before extraction. The bundled client is the established
`0.7.11-zzinstall1` local variant of AmiPkg, with custom-recipe, assign-path,
resolved-receipt and preflight-before-upgrade fixes. Client source, patch and
Apache notices accompany the release source bundle. This is not an upstream
AmiPkg release.

Packaging scripts: `build_uae4arm_installer.py`, `package_uae4arm_release.py`,
`package_uae4arm_payload.py` and `package_uae4arm_installer.py` in `scripts/`.
Signing keys are external private inputs and never included in archives.

This remains a development Beta. See the main README for
current runtime limitations; the installer does not extend emulator compatibility.
