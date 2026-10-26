#!/usr/bin/env python3
"""Build the native MUI launcher; player build is a separate explicit step."""
from pathlib import Path
import hashlib,json,subprocess
from amiga import PIN
from uae4arm_version import VERSION, HEADER
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.context/amiga/uae4arm/launcher';OUT.mkdir(parents=True,exist_ok=True)
subprocess.run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64',
    '-v',f'{ROOT}:/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020',
    '-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fstack-usage',
    'amiga/uae4arm/launcher.c','-lamiga','-o',str((OUT/'ZZUAE').relative_to(ROOT))],check=True,cwd=ROOT)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'version':VERSION,'bytes':(OUT/'ZZUAE').stat().st_size,'sha256':sha(OUT/'ZZUAE'),
        'sources':{str(p.relative_to(ROOT)):sha(p) for p in [HEADER, ROOT/'scripts/uae4arm_version.py', ROOT/'amiga/uae4arm/launcher.c',ROOT/'amiga/uae4arm/launcher_config.h',ROOT/'amiga/uae4arm/profiles.h',ROOT/'amiga/uae4arm/joystick.h',ROOT/'amiga/uae4arm/joystick_ui.h',Path(__file__).resolve()]}}
(OUT/'build.json').write_text(json.dumps(record,indent=2)+'\n')
if (ROOT/'launcher.su').exists():(ROOT/'launcher.su').replace(OUT/'launcher.su')
print(json.dumps(record,indent=2))
