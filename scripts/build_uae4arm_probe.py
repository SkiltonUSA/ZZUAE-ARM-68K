#!/usr/bin/env python3
"""Build bounded UAE4ARM CPU diagnostic using the existing XACP lifecycle."""
import json,subprocess,sys,re
from pathlib import Path
from build_uae4arm import ROOT,OUT,SRC,RUN,inside,prepare
from build_zz9000_debug import unpack_elf
from amiga import PIN
prepare()
manifest=json.loads((OUT/'compile.json').read_text())
flags=manifest['flags']+['-I'+inside(OUT)]
for name in ['worker.cpp','mmu.c','mmu.h','mmu_asm.S','mmu_plan.h']:
 text=(ROOT/'amiga/uae4arm/support/core1'/name).read_text()
 if name=='mmu_plan.h':
  moves={'0x40000u':'0x100000u','0x50000u':'0x110000u','0x60000u':'0x120000u','0x80000u':'0x180000u','0x84000u':'0x184000u','0x82000u':'0x182000u','0x82400u':'0x182400u'}
  text=re.sub('|'.join(moves),lambda m:moves[m[0]],text)
 (OUT/name).write_text(text)
common=['-DZZ_BLOCK_SIZE=0x800000','-DZZ_CONTROL=0x180000','-DMB_ALLOCATION=0x800000','-DMB_MMU','-DMB_DCACHE','-Iamiga/uae4arm/support/core1','-Iamiga/arm_debug','-Iamiga/arm_debug/zz9000']
def run(cmd):subprocess.run(cmd,cwd=ROOT,check=True)
objects=[]
for source in [SRC/'cpu_probe.cpp',OUT/'worker.cpp',OUT/'mmu.c',OUT/'mmu_asm.S',ROOT/'amiga/uae4arm/support/core1/runtime.c']:
 obj=OUT/(source.stem+'.probe.o');objects.append(obj)
 cmd='arm-none-eabi-g++' if source.suffix=='.cpp' else 'arm-none-eabi-gcc'
 opts=flags if source.suffix=='.cpp' else [f for f in flags if f not in ['-std=gnu++11','-fno-exceptions','-fno-rtti','-fpermissive']]
 run([*RUN,cmd,*opts,*common,'-c',inside(source),'-o',inside(obj)])
objects.append(OUT/'cpuemu_11.o')
link=(ROOT/'amiga/uae4arm/support/core1/mmu_payload.ld').read_text().replace('0x40000','0x100000')
(OUT/'probe.ld').write_text(link)
ld='/opt/homebrew/opt/lld/bin/ld.lld'
elf=OUT/'uae-probe.elf'
run([ld,'-shared','-Bsymbolic','--no-undefined','--gc-sections','-T',str(OUT/'probe.ld'),*[str(x) for x in objects],'-o',str(elf)])
payload,relocations,entry=unpack_elf(elf.read_bytes(),0x100000)
run(['clang','--target=arm-none-eabi','-mcpu=cortex-a9','-marm','-c','amiga/arm_debug/zz9000/mapping_probe.S','-o',str(OUT/'mapping.o')])
run([ld,'-shared','-Bsymbolic','--no-undefined','-T','amiga/arm_debug/zz9000/payload.ld',str(OUT/'mapping.o'),'-o',str(OUT/'mapping.elf')])
mapping,rel,point=unpack_elf((OUT/'mapping.elf').read_bytes());assert not rel and not point
array=lambda name,data:'static const unsigned char '+name+'[]={'+','.join(map(str,data))+'};\n'
(OUT/'zz_payload.h').write_text(f'#define ZZ_ENTRY {entry}u\n'+array('zz_image',payload)+array('zz_mapping_probe',mapping)+'static const unsigned long zz_relocations[]={'+','.join(map(str,relocations))+'};\n')
host=(ROOT/'amiga/uae4arm/support/core1/host.c').read_text().replace('MESEN','UAE').replace('8991','26000').replace('value(0) || value(1)','value(0)!=26000 || value(1)')
(OUT/'probe_host.c').write_text(host)
(OUT/'expected.h').write_text('#define UAE_EXPECT_CYCLES 234000u\n#define UAE_EXPECT_HASH 11000u\n')
run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64','-v',str(ROOT)+':/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror',*common,'-DZZ_HEADLESS_BENCH','-DZZ_RELEASE','-DZZ_HEADLESS_MMU','-DZZ_HEADLESS_ICACHE','-DZZ_APP_NAME="ZZUAEProbe"','-DZZ_APP_VERSION="0.1"','-DZZ_MIN_STACK=65536','-I'+str(OUT.relative_to(ROOT)),'amiga/arm_debug/zz9000/launcher.c',str((OUT/'probe_host.c').relative_to(ROOT)),'-lamiga','-o',str((OUT/'ZZUAEProbe').relative_to(ROOT))])
print('Built CPU diagnostic',len(payload),'ARM bytes; relocations',len(relocations))
