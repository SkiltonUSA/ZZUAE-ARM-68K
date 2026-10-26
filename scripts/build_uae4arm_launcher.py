#!/usr/bin/env python3
"""Build the native MUI launcher; player build is a separate explicit step."""
from pathlib import Path
import hashlib,json,subprocess
from amiga import PIN
from uae4arm_version import VERSION, HEADER
from prepare_uae4arm_art import prepare_png
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.context/amiga/uae4arm/launcher';OUT.mkdir(parents=True,exist_ok=True)
prepare_png(ROOT/'amiga/uae4arm/assets/zzuae-logo.png','ZZUAE',OUT)
subprocess.run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64',
    '-v',f'{ROOT}:/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020',
    '-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fstack-usage',
    '-I'+str(OUT.relative_to(ROOT)),'amiga/uae4arm/launcher.c','-lamiga','-o',str((OUT/'ZZUAE').relative_to(ROOT))],check=True,cwd=ROOT)
subprocess.run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64',
    '-v',f'{ROOT}:/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020',
    '-O2','-Wall','-Wextra','-Werror','-I'+str(OUT.relative_to(ROOT)),
    'amiga/uae4arm/icon.c','-lamiga','-o',str((OUT/'ZZUAE-MakeIcon').relative_to(ROOT))],check=True,cwd=ROOT)
scanout=OUT/'Scanlines';scanout.mkdir(exist_ok=True)
for source,name,dest in [('scanlines/vendor/ZZScanlines.c','ZZScanlines',scanout),
                         ('scanlines/vendor/ZZScanlinesGUI.c','ZZScanlinesGUI',scanout),
                         ('install_scanlines.c','Install-Scanlines',OUT)]:
 subprocess.run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64',
    '-v',f'{ROOT}:/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=gnu99','-noixemul','-m68020',
    '-O2','-Wall','-Wextra','amiga/uae4arm/'+source,'-lamiga','-o',str((dest/name).relative_to(ROOT))],check=True,cwd=ROOT)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'version':VERSION,'icon_sha256':sha(OUT/'ZZUAE-MakeIcon'),'scanlines':{p.name:sha(p) for p in [scanout/'ZZScanlines',scanout/'ZZScanlinesGUI',OUT/'Install-Scanlines']},'bytes':(OUT/'ZZUAE').stat().st_size,'sha256':sha(OUT/'ZZUAE'),
        'sources':{str(p.relative_to(ROOT)):sha(p) for p in [HEADER, ROOT/'scripts/uae4arm_version.py', ROOT/'amiga/uae4arm/launcher.c',ROOT/'amiga/uae4arm/splash.h',ROOT/'amiga/uae4arm/icon.c',ROOT/'amiga/uae4arm/install_scanlines.c',*sorted((ROOT/'amiga/uae4arm/scanlines/vendor').glob('*.c')),ROOT/'amiga/uae4arm/assets/zzuae-logo.png',ROOT/'scripts/prepare_uae4arm_art.py',ROOT/'amiga/uae4arm/launcher_config.h',ROOT/'amiga/uae4arm/disk_check.h',ROOT/'amiga/uae4arm/profiles.h',ROOT/'amiga/uae4arm/joystick.h',ROOT/'amiga/uae4arm/joystick_ui.h',Path(__file__).resolve()]}}
(OUT/'build.json').write_text(json.dumps(record,indent=2)+'\n')
if (ROOT/'launcher.su').exists():(ROOT/'launcher.su').replace(OUT/'launcher.su')
print(json.dumps(record,indent=2))
