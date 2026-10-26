#!/usr/bin/env python3
"""Rebuild selected existing picolibc archive members as PIC soft-float C."""
from pathlib import Path
import re,subprocess,shutil,hashlib,json
root=Path(__file__).resolve().parents[1];out=root/'.context/amiga/pocketsnes';src=root/'.context/amiga/ffmpeg-bench/picolibc-1.8.12';objs=out/'libc';objs.mkdir(exist_ok=True)
archive=out/'libc.a'
if not archive.exists():shutil.copyfile(root/'.context/amiga/ffmpeg-bench/libc-pic.a',archive)
files={str(p.relative_to(src)).replace('/','_')+'.o':p for p in src.rglob('*.c')}
manifest=json.loads((root/'amiga/pocketsnes/libc-sources.json').read_text())['members']
members=sorted(manifest)
cmd=['podman','--connection','nuflix-converter-root','exec','zzffmpeg-toolchain']
def inside(p):return '/work/'+str(p.relative_to(root))
flags=['-mcpu=cortex-a9','-marm','-mfloat-abi=soft','-mno-unaligned-access','-Os','-D_LIBC','-D_GNU_SOURCE','-U_FORTIFY_SOURCE','-fPIC','-fno-builtin','-ffunction-sections','-fdata-sections','-include','/work/amiga/pocketsnes/libc_config.h']
flags+=['-I'+inside(src/p) for p in ['libc/tinystdio','libc/locale','libc/stdio','libc/stdlib','libm/common','libm/math']]
for name in members:
 p=files.get(name)
 if name=='libm_machine_arm_sf_fabs.c.o':p=src/'libm/math/sf_fabs.c'
 if not p:
  p=src/'libc/string'/name.replace('.S.o','.c').replace('.c.o','.c')
 assert p.is_file() and str(p.relative_to(src))==manifest[name]['path'],name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest[name]['sha256'],name
 obj=objs/name;stamp=obj.with_suffix('.sha256');digest=hashlib.sha256(p.read_bytes()+str(flags).encode()).hexdigest()
 if stamp.exists() and stamp.read_text()==digest:continue
 print('libc',name,flush=True)
 subprocess.run([*cmd,'arm-none-eabi-gcc',*flags,'-c',inside(p),'-o',inside(obj)],check=True)
 subprocess.run([*cmd,'arm-none-eabi-ar','r',inside(archive),inside(obj)],check=True);stamp.write_text(digest)
(out/'libc-members.json').write_text(json.dumps(members,indent=2)+'\n')
