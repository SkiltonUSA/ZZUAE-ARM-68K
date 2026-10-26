#!/usr/bin/env python3
"""Build an experimental amipkg LHA + recipe from a clean emulator release ZIP."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

from uae4arm_mklha import entry


def amiga_path(value):
    # These paths are also embedded in quoted AmigaDOS script arguments.
    if not re.fullmatch(r"[A-Za-z0-9_-]+:[A-Za-z0-9_ /.-]+", value):
        raise ValueError("Use an absolute Amiga drawer without script metacharacters")
    if any(part in ("", ".", "..") for part in value.split(":", 1)[1].split("/")):
        raise ValueError("Destination must name a drawer, without relative components")
    if len(value) > 160:
        raise ValueError("Destination is too long")
    return value


def package(source, output, app, version, url, destination=None, scanline_destination=None):
    destination = amiga_path(destination or "SYS:Programs/" + app)
    if scanline_destination:
        scanline_destination = amiga_path(scanline_destination)
    required = {app, app + ".info", "Install-Scanlines", "Scanlines/ZZScanlines",
                "Scanlines/ZZScanlinesGUI", "Scanlines/Source/vendor/LICENSE"}
    files = {}
    with zipfile.ZipFile(source) as archive:
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != app or any(c in info.filename for c in "\\:\r\n"):
                raise ValueError("Unexpected archive path: " + info.filename)
            if info.is_dir():
                continue
            relative = path.relative_to(app)
            if (relative.parts[0].lower() in {"roms", "disks", "states", "snapshots", "screenshots"}
                    or relative.name.lower().startswith("library.cfg")
                    or relative.suffix.lower() in {".nes", ".sfc", ".smc", ".sav", ".zzs", ".rom", ".adf", ".cfg", ".man"}):
                raise ValueError("User data must not enter a package: " + str(relative))
            if info.filename in files:
                raise ValueError("Duplicate archive member: " + info.filename)
            files[info.filename] = archive.read(info)
    if len(files) >= 256:
        raise ValueError("Package exceeds amipkg receipt capacity including drawer icon")
    missing = required - {str(PurePosixPath(name).relative_to(app)) for name in files}
    if missing:
        raise ValueError("Incomplete scanline bundle: " + ", ".join(sorted(missing)))
    for name in [app, "Install-Scanlines", "Scanlines/ZZScanlines", "Scanlines/ZZScanlinesGUI"]:
        if files[app + "/" + name][:4] != bytes.fromhex("000003f3"):
            raise ValueError("Not an Amiga executable: " + name)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", version):
        raise ValueError("Invalid version")
    if not url.startswith(("https://", "http://")):
        raise ValueError("Archive URL must be HTTP or HTTPS")
    output.mkdir(parents=True, exist_ok=True)
    lha = output / (app + "-" + version + ".lha")
    with lha.open("wb") as stream:
        for name, data in sorted(files.items()):
            stream.write(entry(name, data))
        stream.write(b"\0")
    command = '"' + destination + '/Install-Scanlines"'
    if scanline_destination:
        command += ' "' + scanline_destination + '"'
    manifest = dict(
        id=app.lower(), name=app, version=version,
        description=app + " with bundled install-missing Xanxi scanline tools",
        category="Emulation", tier="A",
        archive=dict(url=url, mirrors=[], sizeBytes=lha.stat().st_size,
                     sha256=hashlib.sha256(lha.read_bytes()).hexdigest()),
        requirements=dict(minCPU="68020", minKS="3.1"), deps=[], conflicts=[], provides=[],
        requiredCapabilities=["copy-tree-v1", "drawer-icon-v1", "pre-post-script-v1"],
        recipe=dict(recipeSchema=2, ops=[
            dict(op="copyTree", src=app, dest=destination),
            dict(op="drawerIcon", dest=destination + ".info"),
            dict(op="postScript", lines=["FailAt 10", "Stack 32768", command]),
        ]),
    )
    (output / (app.lower() + ".json")).write_text(json.dumps(manifest, indent=2) + "\n")
    return lha, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--app", choices=["ZZUAE"], required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--url", required=True, help="Final URL of the generated LHA")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--destination", help="Default SYS:Programs/<app>; encoded in recipe")
    parser.add_argument("--scanline-destination", help="Isolated tests only; default checks SYS: and C:")
    args = vars(parser.parse_args())
    lha, manifest = package(**args)
    print(lha)
    print(manifest["archive"]["sha256"])
    print("Experimental recipe: see docs/package-manager.md before publishing.")


if __name__ == "__main__":
    main()
