#!/usr/bin/env python3
"""Build isolated guest-JIT tests or --player; preserve the normal player."""
import hashlib,json,re,shutil,subprocess,sys
import build_uae4arm as b
HARDWARE='--hardware' in sys.argv
PLAYER='--player' in sys.argv
ROOT=b.ROOT; NORMAL=b.OUT; OUT=NORMAL/'jit-execution'; SRC=b.SRC
b.OUT=OUT
original_prepare=b.prepare

def prepare():
    tree=original_prepare()
    config=OUT/'include/sysconfig.h'
    config.write_text(config.read_text()+'\n#undef CPUEMU_68000_ONLY\n#define JIT 1\n#define CPUEMU_40 1\n#undef USE_JIT_FPU\n#undef ARM_HAS_DIV\n')
    header=tree/'include/newcpu.h'
    header.write_text(header.read_text().replace('#define MAX_JIT_CACHE 16384','#define MAX_JIT_CACHE 512'))
    cpu=tree/'newcpu.cpp';s=cpu.read_text()
    s=s.replace('{NULL,NULL,op_smalltbl_12_ff}, {NULL,NULL,NULL}, {NULL,NULL,NULL},','{NULL,NULL,op_smalltbl_12_ff}, {NULL,NULL,NULL}, {op_smalltbl_3_ff,op_smalltbl_43_ff,NULL},')
    if PLAYER:s+='\n'+(SRC/'jit_dispatch.inc').read_text()
    cpu.write_text(s)
    port=tree/'jit';shutil.copytree(b.UP/'src/jit',port,dirs_exist_ok=True)
    support=port/'compemu_support.cpp';s=support.read_text()
    start=s.index('static void cache_free (');end=s.index('\n#endif',start)
    s=s[:start]+'''extern "C" void *zzuae_jit_alloc_executable(unsigned);
extern "C" void zzuae_jit_free_executable(void*,unsigned);
static void cache_free(uae_u8 *p,int n){zzuae_jit_free_executable(p,n);}
static uae_u8 *cache_alloc(int n){return (uae_u8*)zzuae_jit_alloc_executable(n);}
'''+s[end:]
    # Bound traces and disable following constant jumps in this diagnostic.
    # Integer divide on A9 normally emits VFP: retain interpreter semantics
    # until the non-local-exit FP context contract is implemented.
    s=s.replace('#define follow_const_jumps (true)','#define follow_const_jumps (false)')
    # Exec-owned guest banks are not a Linux natmem mapping. Generated data
    # accesses and indirect PC translation must consult the bank callbacks.
    s=s.replace('special_mem = pc_hist[i].specmem;', 'special_mem = pc_hist[i].specmem | S_READ | S_WRITE;')
    s=s.replace('if (special_mem & S_READ)','if (true)').replace('if (special_mem & S_WRITE)','if (true)').replace('if (special_mem)','if (true)')

    marker='  /* Initialise state */'
    s=s.replace(marker,'''  for(unsigned op=0;op<65536;op++)
    if(table68k[op].mnemo==i_DIVU || table68k[op].mnemo==i_DIVS || table68k[op].mnemo==i_DIVL)
      compfunctbl[op]=nfcompfunctbl[op]=NULL;
'''+marker)
    s=s.replace('void compile_block(cpu_history*', 'unsigned zz_jit_translated=0,zz_jit_fallback=0;\nvoid compile_block(cpu_history*')
    s=s.replace('        if (failure) {','        if(!failure)++zz_jit_translated;\n        if (failure) {\n          ++zz_jit_fallback;')
    # Bare-metal payload has no global constructors/destructors. BSS starts
    # zeroed; release allocator pools explicitly during compiler shutdown.
    s=s.replace('  LazyBlockAllocator() : mPools(0), mChunks(0) { }','  LazyBlockAllocator() = default;')
    s=s.replace('  ~LazyBlockAllocator();','  void reset();').replace('LazyBlockAllocator<T>::~LazyBlockAllocator()', 'void LazyBlockAllocator<T>::reset()')
    s=s.replace('    free(deadPool);\n  }\n}', '    free(deadPool);\n  }\n  mPools=0;mChunks=0;\n}')
    s=s.replace('void compiler_exit(void)\n{','void compiler_exit(void)\n{\n  BlockInfoAllocator.reset();ChecksumInfoAllocator.reset();')
    support.write_text(s+"\n"+(SRC/"jit_validate.inc").read_text())
    mid=port/'compemu_midfunc_arm.cpp';s=mid.read_text()
    start=s.index('STATIC_INLINE void flush_cpu_icache(');end=s.index('STATIC_INLINE void write_jmp_target',start)
    s=s[:start]+'''extern "C" void zzuae_jit_publish_code(void*,void*);
STATIC_INLINE void flush_cpu_icache(void *a,void *b){zzuae_jit_publish_code(a,b);}
\n'''+s[end:];mid.write_text(s)
    # The ARMv6 byte-MOVE fallback masks into WORK1, then accidentally merges
    # WORK2 in four register-destination paths. Preserve the untouched high
    # bytes and merge the register actually prepared by each path.
    moves=port/'compemu_midfunc_arm2.cpp';s=moves.read_text()
    start=s.index('MIDFUNC(2,jnf_MOVE_b_imm,');end=s.index('MIDFUNC(2,jff_MOVE_w,',start)
    section=s[start:end]
    assert section.count('ORR_rrr(d, d, REG_WORK2);')==4
    s=s[:start]+section.replace('ORR_rrr(d, d, REG_WORK2);','ORR_rrr(d, d, REG_WORK1);')+s[end:]
    moves.write_text(s)
    for p in port.iterdir():
        if p.suffix in {'.cpp','.h'}:p.write_text(re.sub(r'\b_B\b','ZZ_ARM_BRANCH_B',p.read_text()))
    codegen=port/'codegen_arm.h';s=codegen.read_text();start=s.index('#define IMM32(c)');end=s.index('\n\n',start)
    s=s[:start]+s[start:end].replace('((c)','((uae_u32)(c)')+s[end:];codegen.write_text(s)
    header=port/'compemu.h';header.write_text(header.read_text().replace('#define MAXRUN 1024','#define MAXRUN 32'))
    return tree
b.prepare=prepare
# Rebuild all units with the same JIT regstruct ABI, in a separate directory.
sys.argv=[sys.argv[0],'cpuemu_0','cpuemu_11','cpuemu_40','cpustbl','cpudefs','readcpu','newcpu','newcpu_common','custom','cia','events','memory','blitter','blitfunc','blittable','drawing','audio','gfxutil','keybuf','disk','diskutil','rommgr','cfgfile','crc32','inputdevice','rtc']
if b.build():raise SystemExit(1)
flags=json.loads((OUT/'compile.json').read_text())['flags']+['-I'+b.inside(OUT/'src/jit'),'-I/work/amiga/uae4arm/support/core1','-I/work/amiga/arm_debug']
platform=OUT/'platform.cpp';s=(SRC/'machine_platform.cpp').read_text()
s=s.replace('p->cpu_model=68000;p->cpu_compatible=true;p->cachesize=0;', 'p->cpu_model=68020;p->cpu_compatible=false;p->cachesize=512;')
s+='\nvoid jit_abort(const char*,...){abort();}\n\n'
platform.write_text(s)
sources=[platform,SRC/'jit_guest.cpp',SRC/'jit_fault.cpp',SRC/'jit_fault.S',SRC/'jit_cache.cpp',SRC/'live_arm.cpp',SRC/'profile.cpp',SRC/'media.cpp',ROOT/'amiga/uae4arm/support/allocator/heap.c',ROOT/'amiga/uae4arm/support/memory/memory.c',SRC/'runtime.c',SRC/'jump.S']+[OUT/'src/jit'/(n+'.cpp') for n in ['compemu','compstbl','compemu_support']]
objects=[OUT/(n+'.o') for n in sys.argv[1:]]
for source in sources:
    obj=OUT/('guest-'+source.name+'.o');cpp=source.suffix=='.cpp'
    opts=flags if cpp else [f for f in flags if f not in ['-std=gnu++11','-fno-exceptions','-fno-rtti','-fpermissive']]
    dependencies=[p for folder in [SRC,OUT/'src/include',OUT/'src/jit'] for p in sorted(folder.glob('*.h'))]
    dependencies+=sorted((OUT/'src/jit').glob('*.cpp'))
    key=hashlib.sha256(source.read_bytes()+str(opts).encode()+b''.join(p.read_bytes() for p in dependencies)).hexdigest()
    stamp=obj.with_suffix('.sha256')
    if not stamp.exists() or stamp.read_text()!=key:
        r=subprocess.run([*b.RUN,'arm-none-eabi-g++' if cpp else 'arm-none-eabi-gcc',*opts,'-c',b.inside(source),'-o',b.inside(obj)],capture_output=True,text=True)
        (obj.with_suffix('.log')).write_text(r.stdout+r.stderr)
        if r.returncode:print(r.stderr[-6000:]);raise SystemExit(r.returncode)
        stamp.write_text(key)
    objects.append(obj)
# The allocation base need not be page-aligned. The page intersecting the end
# of the shared range stays NC/shareable; keep private atomics beyond it.
link=(NORMAL/'machine.ld').read_text().replace('.bss 0x640000 (NOLOAD) : {', '.bss 0x640000 (NOLOAD) : { . += 0x1000;');(OUT/'guest.ld').write_text(link)
subprocess.run(['/opt/homebrew/opt/lld/bin/ld.lld','-shared','-Bsymbolic','--no-undefined','--gc-sections','--error-limit=0','-T',str(OUT/'guest.ld'),*map(str,objects),'--exclude-libs=ALL',str(ROOT/'.context/amiga/uae4arm/libc/libc.a'),str(NORMAL/'libgcc.a'),'-o',str(OUT/'guest.elf')],check=True)
print('Built isolated guest JIT diagnostic',OUT/'guest.elf')

if PLAYER:
    # Reuse the normal transport/display/audio build with the matching JIT ABI.
    import runpy
    for name in ['libgcc.a','mapping.elf']:shutil.copy2(NORMAL/name,OUT/name)
    b.prepare=lambda: OUT/'src'
    sys.argv=['build_uae4arm_machine.py','--guest-jit']+(['--hardware'] if HARDWARE else [])
    runpy.run_path(str(ROOT/'scripts/build_uae4arm_machine.py'),run_name='__main__')

if HARDWARE and not PLAYER:
    from amiga import PIN as COMPILER
    from build_zz9000_debug import unpack_elf
    import importlib.util
    hw=OUT/'hardware';hw.mkdir(exist_ok=True)
    common=['-DZZ_BLOCK_SIZE=0x2000000','-DZZ_CONTROL=0x480000','-DMB_ALLOCATION=0x2000000u','-DMB_MMU','-DMB_DCACHE']
    for name in ['worker.cpp','mmu.c','mmu.h','mmu_asm.S','mmu_plan.h']:
        data=(ROOT/'amiga/uae4arm/support/core1'/name).read_text()
        if name=='mmu_plan.h':
            moves={'0x40000u':'0x400000u','0x50000u':'0x420000u','0x60000u':'0x430000u','0x80000u':'0x480000u','0x84000u':'0x640000u','0x82000u':'0x482000u','0x82400u':'0x482400u'}
            data=re.sub('|'.join(moves),lambda m:moves[m[0]],data)
        if name=='worker.cpp':data='#include "machine.h"\n'+data.replace('    shared=base;','    shared=base;zzuae_shared(base);')
        (hw/name).write_text(data)
    hwobjects=objects.copy()
    for name in ['worker.cpp','mmu.c','mmu_asm.S']:
        source=hw/name;obj=hw/(name+'.o');cpp=source.suffix=='.cpp'
        opts=flags if cpp else [f for f in flags if f not in ['-std=gnu++11','-fno-exceptions','-fno-rtti','-fpermissive']]
        subprocess.run([*b.RUN,'arm-none-eabi-g++' if cpp else 'arm-none-eabi-gcc','-I'+b.inside(hw),'-I/work/amiga/arm_debug/zz9000',*opts,*common,'-c',b.inside(source),'-o',b.inside(obj)],check=True)
        hwobjects.append(obj)
    (hw/'payload.ld').write_text(link.replace('ENTRY(mesen_test)','ENTRY(_start)'))
    elf=hw/'guest.elf'
    subprocess.run(['/opt/homebrew/opt/lld/bin/ld.lld','-shared','-Bsymbolic','--no-undefined','--gc-sections','-T',str(hw/'payload.ld'),*map(str,hwobjects),'--exclude-libs=ALL',str(ROOT/'.context/amiga/uae4arm/libc/libc.a'),str(NORMAL/'libgcc.a'),'-o',str(elf)],check=True)
    spec=importlib.util.spec_from_file_location('jitelf',SRC/'elf.py');packer=importlib.util.module_from_spec(spec);spec.loader.exec_module(packer)
    payload,relocations,entry=packer.unpack(elf.read_bytes())
    mapping,rel,point=unpack_elf((NORMAL/'mapping.elf').read_bytes());assert not rel and not point
    array=lambda name,data:'static const unsigned char '+name+'[]={'+','.join(map(str,data))+'};\n'
    (hw/'zz_payload.h').write_text(f'#define ZZ_ENTRY {entry}u\n'+array('zz_image',payload)+array('zz_mapping_probe',mapping)+'static const unsigned long zz_relocations[]={'+','.join(map(str,relocations))+'};\n')
    host=(ROOT/'amiga/uae4arm/support/core1/host.c').read_text().replace('#include "expected.h"','').replace('rate,i;','rate;').replace('MESEN CPU-ONLY','ZZUAE GUEST-JIT CPU-ONLY')
    start=host.index('    if(!request(MB_VERIFY))');end=host.index('\ndone:',start)
    host=host[:start]+r'''    if(!request(MB_VERIFY)){
        io->pull(base+0x482a40,32,NULL);
        printf("JIT_FAULT magic=%08x type=%u lr=%08x cpsr=%08x dfsr=%08x ifsr=%08x dfar=%08x ifar=%08x\n",ad_get(base,0x482a40),ad_get(base,0x482a44),ad_get(base,0x482a48),ad_get(base,0x482a4c),ad_get(base,0x482a50),ad_get(base,0x482a54),ad_get(base,0x482a58),ad_get(base,0x482a5c));goto done;
    }
    printf("JIT_GUEST checked=%u mismatch=%08x fallback_sites=%u hash=%08x errors=%u translated_sites=%u ticks=%u cpu_us=%u\n",value(0),value(1),value(2),value(3),value(4),value(9),value(6),(ULONG)((uint64_t)value(6)*1000000u/rate));
    if(value(0)!=240 || value(1) || value(4) || !value(9) || !value(2))goto done;
    puts("JIT_GUEST PASS; CPU differential fixture, NOT Workbench/game JIT");fflush(stdout);rc=0;
'''+host[end:]
    (hw/'host.c').write_text(host)
    includes=['-I'+str(hw.relative_to(ROOT)),'-Iamiga/uae4arm','-Iamiga/uae4arm/support/core1','-Iamiga/arm_debug','-Iamiga/arm_debug/zz9000']
    subprocess.run(['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64','-v',str(ROOT)+':/work','-w','/work',COMPILER['image'],'m68k-amigaos-gcc','-std=c99','-noixemul','-m68020','-O2','-Wall','-Wextra','-Werror',*common,*includes,'-DZZ_HEADLESS_BENCH','-DZZ_RELEASE','-DZZ_HEADLESS_MMU','-DZZ_HEADLESS_ICACHE','-DZZ_APP_NAME="ZZUAEJIT"','-DZZ_APP_VERSION="0.5.4-dev"','-DZZ_MIN_STACK=131072','amiga/arm_debug/zz9000/launcher.c',str((hw/'host.c').relative_to(ROOT)),'-lamiga','-o',str((hw/'ZZUAEJIT').relative_to(ROOT))],check=True)
    print('Built bounded hardware guest-JIT diagnostic',len(payload),'ARM bytes')
