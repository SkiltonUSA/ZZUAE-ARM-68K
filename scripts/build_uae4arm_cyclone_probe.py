#!/usr/bin/env python3
"""Build isolated A9 Cyclone step/batch probes; never replace a player.

Requires the normal ZZUAE core build. Cyclone is pinned and built as GPLv2.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path
from build_uae4arm import ROOT, OUT as NORMAL, RUN, inside
from build_zz9000_debug import unpack_elf
from amiga import PIN
REV='fe89d4e2fb7b876ec71d7a8ce66affbbdf91104d'
BIG_ENDIAN='--big-endian' in sys.argv
OUT=NORMAL/('cyclone-probe-be' if BIG_ENDIAN else 'cyclone-probe')
UP=ROOT/'.context/cyclone-review'

def run(cmd, **kwargs):
    subprocess.run(cmd,cwd=ROOT,check=True,**kwargs)

def main():
    if not UP.exists():
        run(['git','clone','https://github.com/notaz/cyclone68000',str(UP)])
        run(['git','-C',str(UP),'checkout','--detach',REV])
    assert subprocess.check_output(['git','-C',str(UP),'rev-parse','HEAD'],text=True).strip()==REV
    OUT.mkdir(parents=True,exist_ok=True)
    gen=OUT/'generator';gen.mkdir(exist_ok=True)
    for p in UP.iterdir():
        if p.suffix in ('.cpp','.h') or p.name in ('Makefile','Disa'):
            if p.is_dir():shutil.copytree(p,gen/p.name,dirs_exist_ok=True)
            else:shutil.copy2(p,gen/p.name)
    if BIG_ENDIAN:
        from prepare_uae4arm_cyclone import big_endian_fetches, movem_address_error
        big_endian_fetches(gen)
        if '--fix-movem' in sys.argv:movem_address_error(gen)
    config=(gen/'config.h').read_text()
    for name in ('USE_INT_ACK_CALLBACK','USE_RESET_CALLBACK','EMULATE_ADDRESS_ERRORS_IO','EMULATE_HALT'):
        config=re.sub(r'(#define '+name+r'\s+)0',r'\g<1>1',config)
    (gen/'config.h').write_text(config)
    run(['make','-C',str(gen),'HAVE_ARMv6T2=1','CXXFLAGS=-O2 -DHAVE_ARMv6T2=1 -DHAVE_UNALIGNED_ACCESSES=0'])
    flags=json.loads((NORMAL/'compile.json').read_text())['flags']+(['-DCYCLONE_BIG_ENDIAN'] if BIG_ENDIAN else [])+['-I'+inside(OUT),'-I'+inside(gen)]
    common=['-DZZ_BLOCK_SIZE=0x800000','-DZZ_CONTROL=0x180000','-DMB_ALLOCATION=0x800000','-DMB_MMU','-DMB_DCACHE','-Iamiga/uae4arm/support/core1','-Iamiga/arm_debug','-Iamiga/arm_debug/zz9000']
    for name in ['worker.cpp','mmu.c','mmu.h','mmu_asm.S','mmu_plan.h']:
        text=(ROOT/'amiga/uae4arm/support/core1'/name).read_text()
        if name=='mmu_plan.h':
            moves={'0x40000u':'0x100000u','0x50000u':'0x110000u','0x60000u':'0x120000u','0x80000u':'0x180000u','0x84000u':'0x184000u','0x82000u':'0x182000u','0x82400u':'0x182400u'}
            text=re.sub('|'.join(moves),lambda m:moves[m[0]],text)
        (OUT/name).write_text(text)
    objects=[]
    for source in [OUT/'worker.cpp',OUT/'mmu.c',OUT/'mmu_asm.S',ROOT/'amiga/uae4arm/support/core1/runtime.c',gen/'Cyclone.s']:
        obj=OUT/(source.stem+'.o');objects.append(obj)
        cpp=source.suffix=='.cpp'
        opts=flags if cpp else [f for f in flags if f not in ['-std=gnu++11','-fno-exceptions','-fno-rtti','-fpermissive']]
        run([*RUN,'arm-none-eabi-g++' if cpp else 'arm-none-eabi-gcc',*opts,*common,'-c',inside(source),'-o',inside(obj)])
    (OUT/'probe.ld').write_text((ROOT/'amiga/uae4arm/support/core1/mmu_payload.ld').read_text().replace('0x40000','0x100000'))
    ld='/opt/homebrew/opt/lld/bin/ld.lld'
    mapping,rel,point=unpack_elf((NORMAL/'mapping.elf').read_bytes());assert not rel and not point
    array=lambda name,data:'static const unsigned char '+name+'[]={'+','.join(map(str,data))+'};\n'
    for mode in ('step','batch'):
        obj=OUT/('probe-'+mode+'.o')
        run([*RUN,'arm-none-eabi-g++',*flags,*common,*(['-DCYCLONE_BATCH'] if mode=='batch' else []),'-c',inside(ROOT/'amiga/uae4arm/cyclone/probe.cpp'),'-o',inside(obj)])
        elf=OUT/(mode+'.elf')
        run([ld,'-shared','-Bsymbolic','-z','notext','--no-undefined','--gc-sections','-T',str(OUT/'probe.ld'),str(obj),*[str(x)for x in objects],'-o',str(elf)])
        payload,relocations,entry=unpack_elf(elf.read_bytes(),0x100000)
        (OUT/'zz_payload.h').write_text(f'#define ZZ_ENTRY {entry}u\n'+array('zz_image',payload)+array('zz_mapping_probe',mapping)+'static const unsigned long zz_relocations[]={'+','.join(map(str,relocations))+'};\n')
        host=(ROOT/'amiga/uae4arm/support/core1/host.c').read_text().replace('MESEN','UAE').replace('8991','26000').replace('value(0) || value(1)','value(0)!=26000 || value(1)')
        (OUT/'probe_host.c').write_text(host)
        (OUT/'expected.h').write_text('#define UAE_EXPECT_CYCLES 234000u\n#define UAE_EXPECT_HASH 11000u\n')
        run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64','-v',str(ROOT)+':/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror',*common,'-DZZ_HEADLESS_BENCH','-DZZ_RELEASE','-DZZ_HEADLESS_MMU','-DZZ_HEADLESS_ICACHE','-DZZ_APP_NAME="ZZCycloneProbe"','-DZZ_APP_VERSION="0.1"','-DZZ_MIN_STACK=65536','-I'+str(OUT.relative_to(ROOT)),'amiga/arm_debug/zz9000/launcher.c',str((OUT/'probe_host.c').relative_to(ROOT)),'-lamiga','-o',str((OUT/('ZZCyclone-'+mode)).relative_to(ROOT))])
        print(mode,len(payload),'ARM bytes',len(relocations),'relocations')
    (OUT/'build.json').write_text(json.dumps(dict(cyclone_revision=REV,flags=flags,config=config),indent=2)+'\n')
if __name__=='__main__':main()
