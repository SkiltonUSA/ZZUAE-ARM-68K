"""Isolated clock-aware FPU build, retaining recorded guest CPU/chipset objects."""
import argparse,hashlib,importlib.util,json,re,shutil,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parents[1],help='Prepared source/toolchain workspace')
p.add_argument('--base',type=Path,required=True,help='Recorded FPU build with manifest, objects and paired MMU sources')
p.add_argument('--output',type=Path,required=True)
p.add_argument('--gameplay-test',action='store_true',help='Diagnostic Banshee input sequence; never install this variant')
p.add_argument('--silent-cadence',action='store_true',help='Isolated sound-off display-cadence candidate; do not install as default')
p.add_argument('--silent-reference',action='store_true',help='Recompile the same display source without the experimental cadence switch')
p.add_argument('--connection',default='nuflix-converter-root')
a=p.parse_args();R=a.workspace.resolve();B=a.base.resolve();O=a.output.resolve()
assert not(a.silent_cadence and a.silent_reference),'Choose one display experiment'
assert O!=B and B not in O.parents,'Keep the recorded build unchanged'
O.relative_to(R);B.relative_to(R);O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'scripts'))
from build_zz9000_debug import unpack_elf
from prepare_uae4arm_clock import host_clock
from prepare_uae4arm_audio_rate import host_audio_rate
# Product identity belongs to this source checkout, not the external toolchain workspace.
vspec=importlib.util.spec_from_file_location('fpu_product_version',Path(__file__).with_name('uae4arm_version.py'))
vmod=importlib.util.module_from_spec(vspec);vspec.loader.exec_module(vmod)
VERSION=vmod.VERSION
from amiga import PIN
j=json.loads((B/'build-manifest.json').read_text());assert j['guest_fpu'] and j['guest_jit']
assert 'ZU_JIT_CACHE_KIB=32768' in str(json.loads((B/'compile.json').read_text())['flags'])
assert '#define ZZ_BLOCK_SIZE' not in (B/'machine/host.c').read_text()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(B/'machine/uae.elf')==j['artifacts']['uae.elf']
flags=[x.replace('/work/',str(R)+'/') for x in json.loads((B/'compile.json').read_text())['flags']]
flags += ['-DZZUAE_GUEST_JIT','-DZZUAE_GUEST_FPU','-DZZUAE_NEON_EXPERIMENT','-DZZUAE_AUDIO_RESERVE','-I'+str(B),'-I'+str(R/'amiga/mesen_bench'),'-I'+str(R/'amiga/arm_debug'),'-I'+str(R/'amiga/arm_debug/zz9000'),'-isystem',str(R/'.tools/uae-picolibc/usr/arm-none-eabi/include'),'-isystem',str(R/'.tools/uae-libstdcxx/usr/include/newlib/c++/14.2.1'),'-isystem',str(R/'.tools/uae-libstdcxx/usr/include/newlib/c++/14.2.1/arm-none-eabi')]
run=lambda cmd:subprocess.run(list(map(str,cmd)),cwd=R,check=True)
platform=R/'amiga/uae4arm/machine_platform.cpp'
if a.gameplay_test:
    text='extern "C" void zzuae_live_event(unsigned,int);\n'+platform.read_text()
    old='if(uae_input_mode && (timeframes==900 || timeframes==910))\n  zzuae_test_button(uae_input_mode,timeframes==900);'
    assert text.count(old)==1
    # Guest-frame input: unaffected by host loading time or render frame skips.
    new='''if(uae_input_mode){
      const unsigned clicks[]={1800,2800};
      const unsigned fires[]={3200,4000,4800};
      for(unsigned f:clicks)if(timeframes==f || timeframes==f+10)zzuae_live_event(4,timeframes==f);
      for(unsigned f:fires)if(timeframes==f || timeframes==f+10)zzuae_live_event(6,4|(timeframes==f?0:128));
      if(timeframes==3400 || timeframes==3450)zzuae_live_event(6,timeframes==3400?0:128);
      if(timeframes==3600 || timeframes==3650)zzuae_live_event(6,1|(timeframes==3600?0:128));
    }'''
    platform=O/'gameplay-platform.cpp';platform.write_text(text.replace(old,new))
run(['arm-none-eabi-g++',*flags,'-c',platform,'-o',O/'platform.o'])
names=['machine_probe.o','bitplanes_neon.o','machine-machine_platform.cpp.o','machine-live_arm.cpp.o','machine-profile.cpp.o','machine-media.cpp.o','machine-storage_arm.cpp.o','machine-heap.c.o','machine-memory.c.o','machine-runtime.c.o','machine-jump.S.o','machine-convert_neon.S.o','machine-jit_cache.cpp.o','machine-jit_fault.cpp.o','machine-jit_fault.S.o','machine-fpu_runtime.cpp.o']
names += [n+'.o' for n in 'cpuemu_11 cpustbl cpudefs readcpu newcpu newcpu_common custom cia events memory blitter blitfunc blittable drawing audio gfxutil keybuf disk diskutil rommgr cfgfile crc32 inputdevice rtc ide fpp fpu_state cpuemu_0 cpuemu_40 guest-compemu.cpp guest-compstbl.cpp guest-compemu_support.cpp'.split()]
objects=[O/'platform.o' if n=='machine-machine_platform.cpp.o' else B/n for n in names]
if a.silent_cadence or a.silent_reference:
    source_root=Path(__file__).resolve().parents[1]
    live=source_root/'amiga/uae4arm/live_arm.cpp'
    run(['arm-none-eabi-g++',*flags,*(['-DZZUAE_SILENT_CADENCE'] if a.silent_cadence else []),'-c',live,'-o',O/'live.o'])
    objects=[O/'live.o' if n=='machine-live_arm.cpp.o' else obj for n,obj in zip(names,objects)]
archives=[R/'.context/amiga/pocketsnes/libc.a',B/'libgcc.a']
for archive in archives:assert sha(archive)==j['archives'][str(archive.relative_to(R))]
for name,link,objs in [('uae-machine.elf',B/'machine.ld',objects),('uae.elf',B/'machine/payload.ld',objects+[B/'machine'/n for n in ('worker.cpp.o','mmu.c.o','mmu_asm.S.o')])]:
 run(['/opt/homebrew/opt/lld/bin/ld.lld','-shared','-Bsymbolic','--no-undefined','--gc-sections','-T',link,*objs,'--exclude-libs=ALL',*archives,'-o',O/name])
# Clock adapter must stay integer-only; existing FPU leaves retain recorded code.
audit_objects=[O/'platform.o']+([O/'live.o'] if a.silent_cadence or a.silent_reference else [])
dis=subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-objdump','-d',*audit_objects],text=True)
assert not re.search(r'\t(?:[us]div|v[a-z][a-z0-9.]*)\s',dis)
spec=importlib.util.spec_from_file_location('elf',R/'amiga/uae4arm/elf.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
payload,rel,entry=m.unpack((O/'uae.elf').read_bytes(),allocation_size=0x4800000)
mapping,relmap,point=unpack_elf((B/'mapping.elf').read_bytes());assert not relmap and not point
arr=lambda n,d:'static const unsigned char '+n+'[]={'+','.join(map(str,d))+'};\n'
(O/'zz_payload.h').write_text(f'#define ZZ_ENTRY {entry}u\n'+arr('zz_image',payload)+arr('zz_mapping_probe',mapping)+'static const unsigned long zz_relocations[]={'+','.join(map(str,rel))+'};\n')
for n in ['mmu.h','mmu_plan.h']:shutil.copy2(B/'machine'/n,O/n)
syms={p[2]:int(p[0],16) for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',O/'uae.elf'],text=True).splitlines() if len(p:=line.split())==3}
host=host_audio_rate(host_clock((B/'machine/host.c').read_text()))
if a.silent_cadence:
    shutil.copy2(source_root/'amiga/uae4arm/display_clock.h',O/'display_clock.h')
    marker='        if(audio_mode){\n            if(!(boot_options&UAE_OPT_LIVE))return 20;'
    assert host.count(marker)==1
    host=host.replace(marker,'''        if(!audio_mode){
            struct zu_display_clock clock=zu_display_clock_plan(frame_period,0,ntsc_mode?60:50);
            display_rate=clock.rate;frame_period=clock.period;
        }
'''+marker)
    host='#include "display_clock.h"\n'+host
host=re.sub(r'#define UAE_DISK1_OFFSET \d+u',f'#define UAE_DISK1_OFFSET {syms["zzuae_disk1_image"]}u',host)
host=host.replace('if(live_window)live_poll();','if(live_window){ULONG paused=live_paused_us;live_poll();start+=live_paused_us-paused;}')
anchor='syncio->pull(shared+UAE_OPTIONS+72,24,NULL);';assert host.count(anchor)==1
host=host.replace(anchor,anchor+'\n    if(ad_get(shared,UAE_OPTIONS+80)){puts("ERROR FPU state mismatch");goto done;}')
(O/'host.c').write_text(host)
common=['-DZZUAE_AUDIO_RESERVE','-DZZ_BLOCK_SIZE=75497472','-DZZ_CONTROL=0x480000','-DMB_ALLOCATION=75497472u','-DMB_MMU','-DMB_DCACHE','-DZZ_HEADLESS_BENCH','-DFF_DIRECT','-DZZ_RELEASE','-DZZ_HEADLESS_MMU','-DZZ_HEADLESS_ICACHE','-DZZ_APP_NAME="ZZUAE-FPU"','-DZZ_APP_VERSION="'+VERSION+'"','-DZZ_MIN_STACK=131072','-Dmain=zzuae_main']
for boot,name in [(False,'FPUVerify'),(True,'ZZUAE-FPU')]:
 cmd=['podman','--connection',a.connection,'run','--rm','--platform','linux/amd64','-v',str(R)+':/work','-w','/work',PIN['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror',*common,'-I'+str(O.relative_to(R)),'-Iamiga/uae4arm','-Iamiga/mesen_bench','-Iamiga/arm_debug','-Iamiga/arm_debug/zz9000']
 if boot:cmd+=['-DUAE_BOOT','-DZZUAE_SESSION_MENU','amiga/uae4arm/audio_host.c']
 run(cmd+['amiga/arm_debug/zz9000/launcher.c',O.relative_to(R)/'host.c','-lamiga','-o',O.relative_to(R)/name])
(O/'build.json').write_text(json.dumps({'builder_sha256':sha(Path(__file__)),'gameplay_test':a.gameplay_test,'silent_cadence':a.silent_cadence,'silent_reference':a.silent_reference,'silent_sources':{n:sha(source_root/'amiga/uae4arm'/n) for n in ['live_arm.cpp','display_clock.h']} if a.silent_cadence or a.silent_reference else {},'platform_sha256':sha(platform),'version':VERSION,'base':str(B.relative_to(R)),'base_version':j['version'],'base_manifest':sha(B/'build-manifest.json'),'runtime_clock':True,'guest_fpu':True,'runtime_allocation_bytes':0x4800000,'jit_cache_kib':32768,'objects':{str(p.relative_to(R)):sha(p) for p in objects},'sources':{str(p.relative_to(R)):sha(p) for p in [R/'amiga/uae4arm/machine_platform.cpp',R/'amiga/uae4arm/audio_host.c',R/'scripts/prepare_uae4arm_clock.py',R/'scripts/prepare_uae4arm_audio_rate.py',*sorted((R/'amiga/uae4arm').glob('*.h')),*sorted((R/'amiga/uae4arm').glob('*.inc'))]},'artifacts':{n:sha(O/n) for n in ['ZZUAE-FPU','FPUVerify','uae.elf','uae-machine.elf','host.c','mmu.h','mmu_plan.h']}},indent=2)+'\n')
print('Built',O)
