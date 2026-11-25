#!/usr/bin/env python3
"""Rebuild the display adapter around hash-pinned, released 68000/68020 cores."""
import argparse,hashlib,importlib.util,json,re,shutil,subprocess,sys
from pathlib import Path
from prepare_uae4arm_cadence import host_cadence
from prepare_uae4arm_audio_rate import host_audio_rate
from uae4arm_version import VERSION
C=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--workspace',type=Path,required=True)
p.add_argument('--base',type=Path,required=True,help='Recorded display build with build.json and uae.elf')
p.add_argument('--released-player',type=Path,required=True,help='Released executable containing this exact ARM payload')
p.add_argument('--output',type=Path,required=True)
p.add_argument('--reference',action='store_true')
p.add_argument('--connection',default='nuflix-converter-root')
a=p.parse_args();R=a.workspace.resolve();B=a.base.resolve();O=a.output.resolve()
O.relative_to(R);assert O!=B and B not in O.parents,'Keep recorded inputs unchanged'
O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'scripts'))
from amiga import PIN
from build_zz9000_debug import unpack_elf
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
run=lambda cmd:subprocess.run(list(map(str,cmd)),cwd=R,check=True)
j=json.loads((B/'build.json').read_text());assert not j['guest_fpu'] and j['runtime_clock']
base=R/j['base'];old=json.loads((base/'build-manifest.json').read_text())
assert sha(base/'build-manifest.json')==j['base_manifest']
objects=[]
for name,digest in j['objects'].items():
 obj=R/name;assert sha(obj)==digest, 'Recorded object changed: '+name
 objects.append(obj)
archives=[R/'.context/amiga/pocketsnes/libc.a',base/'libgcc.a']
for archive in archives:assert sha(archive)==old['archives'][str(archive.relative_to(R))]
spec=importlib.util.spec_from_file_location('elf',C/'amiga/uae4arm/elf.py');elf=importlib.util.module_from_spec(spec);spec.loader.exec_module(elf)
def link(target,inputs):
 run(['/opt/homebrew/opt/lld/bin/ld.lld','-shared','-Bsymbolic','--no-undefined','--gc-sections','-T',base/'machine/payload.ld',*inputs,'--exclude-libs=ALL',*archives,'-o',target])
link(O/'retained.elf',objects)
original=elf.unpack((B/'uae.elf').read_bytes(),allocation_size=j['runtime_allocation_bytes'])
assert elf.unpack((O/'retained.elf').read_bytes(),allocation_size=j['runtime_allocation_bytes'])==original,'Retained core no longer reproduces'
assert bytes(original[0]) in a.released_player.read_bytes(),'Core does not match released executable'
flags=j['effective_flags'][:]
flags.insert(0,'-I'+str(C/'amiga/uae4arm'))
if not a.reference:flags.append('-DZZUAE_SILENT_CADENCE')
source=C/'amiga/uae4arm/live_arm.cpp';obj=O/'live.o'
run(['arm-none-eabi-g++',*flags,'-c',source,'-o',obj])
assert sum(o.name=='live_arm.o' for o in objects)==1
objects=[obj if o.name=='live_arm.o' else o for o in objects]
link(O/'uae.elf',objects)
# Coroutines preserve integer registers; only the recorded assembly leaves use SIMD.
code=subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-objdump','-d',obj],text=True)
assert not re.search(r'\t(?:[us]div|v[a-z][a-z0-9.]*)\s',code)
payload,rel,entry=elf.unpack((O/'uae.elf').read_bytes(),allocation_size=j['runtime_allocation_bytes'])
mapping,rmap,point=unpack_elf((base/'mapping.elf').read_bytes());assert not rmap and not point
arr=lambda name,data:'static const unsigned char '+name+'[]={'+','.join(map(str,data))+'};\n'
(O/'zz_payload.h').write_text(f'#define ZZ_ENTRY {entry}u\n'+arr('zz_image',payload)+arr('zz_mapping_probe',mapping)+'static const unsigned long zz_relocations[]={'+','.join(map(str,rel))+'};\n')
for name in ['mmu.h','mmu_plan.h']:shutil.copy2(base/'machine'/name,O/name)
syms={x[2]:int(x[0],16) for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',O/'uae.elf'],text=True).splitlines() if len(x:=line.split())==3}
host=host_audio_rate((B/'host.c').read_text());assert 'UAE_TIMER_DIVISOR' in host
host=re.sub(r'#define UAE_DISK1_OFFSET \d+u',f'#define UAE_DISK1_OFFSET {syms["zzuae_disk1_image"]}u',host)
if not a.reference:host=host_cadence(host)
host=host.replace('if(live_window)live_poll();','if(live_window){ULONG paused=live_paused_us;live_poll();start+=live_paused_us-paused;}')
(O/'host.c').write_text(host)
size=j['runtime_allocation_bytes'];common=['-DZZUAE_AUDIO_RESERVE',f'-DZZ_BLOCK_SIZE={size}','-DZZ_CONTROL=0x480000',f'-DMB_ALLOCATION={size}u','-DMB_MMU','-DMB_DCACHE']
if j['rgb565_fullscreen']:common.append('-DZZUAE_RGB565_FULLSCREEN')
relative=lambda f:str(f.relative_to(R))
run(['podman','--connection',a.connection,'run','--rm','--platform','linux/amd64','-v',str(R)+':/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror',*common,'-I'+relative(O),'-I'+relative(C/'amiga/uae4arm'),'-Iamiga/mesen_bench','-Iamiga/arm_debug','-Iamiga/arm_debug/zz9000','-DZZ_HEADLESS_BENCH','-DFF_DIRECT','-DZZ_RELEASE','-DZZ_HEADLESS_MMU','-DZZ_HEADLESS_ICACHE','-DZZ_APP_NAME="ZZUAE"','-DZZ_APP_VERSION="'+VERSION+'"','-DZZ_MIN_STACK=131072','-DUAE_BOOT','-DZZUAE_SESSION_MENU','-Dmain=zzuae_main',relative(C/'amiga/uae4arm/audio_host.c'),'amiga/arm_debug/zz9000/launcher.c',relative(O/'host.c'),'-lamiga','-o',relative(O/'ZZUAE-Player')])
sources=[source,C/'amiga/common/rtg_mapping.h',C/'scripts/prepare_uae4arm_cadence.py',C/'scripts/prepare_uae4arm_audio_rate.py',Path(__file__),*sorted((C/'amiga/uae4arm').glob('*.h')),*sorted((C/'amiga/uae4arm').glob('*.inc')),C/'amiga/uae4arm/audio_host.c',R/'amiga/arm_debug/zz9000/launcher.c']
record={'version':VERSION,'silent_cadence':not a.reference,'guest_jit':j['guest_jit'],'guest_fpu':False,'runtime_allocation_bytes':size,'base':relative(B),'base_manifest':sha(B/'build.json'),'released_player_sha256':sha(a.released_player),'retained_payload_sha256':hashlib.sha256(original[0]).hexdigest(),'retained_reproduced':True,'objects':{relative(o):sha(o) for o in objects},'sources':{relative(s):sha(s) for s in sources},'artifacts':{n:sha(O/n) for n in ['ZZUAE-Player','uae.elf','host.c','mmu.h','mmu_plan.h']}}
(O/'build.json').write_text(json.dumps(record,indent=2)+'\n');print('Built',O)
