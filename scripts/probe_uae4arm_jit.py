#!/usr/bin/env python3
"""Compile-only audit of pinned UAE4ARM ARM JIT; never links or deploys it.

The released compatible-68000 build is untouched. Missing platform services
are reported rather than replaced with fake successful mmap/cache operations.
"""
import json,subprocess,shutil,re
from pathlib import Path
from build_uae4arm import ROOT,UP,OUT,RUN,inside,PIN

assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=UP,text=True).strip()==PIN
dest=OUT/'jit-probe';dest.mkdir(exist_ok=True)
(dest/'sysconfig.h').write_text('#include "'+inside(OUT/'include/sysconfig.h')+'"\n#undef CPUEMU_68000_ONLY\n#define JIT 1\n#undef USE_JIT_FPU\n#undef ARM_HAS_DIV\n')
flags=[f for f in json.loads((OUT/'compile.json').read_text())['flags'] if f!='-DZZUAE_PROFILE']
flags=['-I'+inside(dest),'-I'+inside(UP/'src/jit'),*flags]
results=[]
for name in ['compemu','compstbl','compemu_support']:
    source=UP/'src/jit'/(name+'.cpp');obj=dest/(name+'.o')
    r=subprocess.run([*RUN,'arm-none-eabi-g++',*flags,'-c',inside(source),'-o',inside(obj)],capture_output=True,text=True)
    (dest/(name+'.log')).write_text(r.stdout+r.stderr)
    results.append(dict(unit=name,compiled=r.returncode==0,log=name+'.log'))
    print(name,'COMPILED' if r.returncode==0 else 'PLATFORM PORT REQUIRED',flush=True)
    if r.returncode:print('\n'.join(r.stderr.splitlines()[:12]),flush=True)
(dest/'result.json').write_text(json.dumps(dict(upstream=PIN,scope='compile only, no executable or hardware JIT result',units=results),indent=2)+'\n')
# Isolate platform calls behind declarations to measure the remaining compiler
# port. These hooks deliberately have NO definitions: linking must fail until
# executable owned memory and cache publication are implemented and tested.
port=dest/'platform-audit';shutil.copytree(UP/'src/jit',port,dirs_exist_ok=True)
support=(port/'compemu_support.cpp').read_text()
start=support.index('static void cache_free (');end=support.index('\n#endif',start)
support=support[:start]+'''extern "C" void *zzuae_jit_alloc_executable(unsigned);
extern "C" void zzuae_jit_free_executable(void*,unsigned);
static void cache_free(uae_u8 *p,int n){zzuae_jit_free_executable(p,n);}
static uae_u8 *cache_alloc(int n){return (uae_u8*)zzuae_jit_alloc_executable(n);}
'''+support[end:]
(port/'compemu_support.cpp').write_text(support)
mid=(port/'compemu_midfunc_arm.cpp').read_text()
start=mid.index('STATIC_INLINE void flush_cpu_icache(');end=mid.index('STATIC_INLINE void write_jmp_target',start)
mid=mid[:start]+'''extern "C" void zzuae_jit_publish_code(void*,void*);
STATIC_INLINE void flush_cpu_icache(void *start,void *stop){zzuae_jit_publish_code(start,stop);}
\n'''+mid[end:]
(port/'compemu_midfunc_arm.cpp').write_text(mid)
for p in port.iterdir():
    if p.suffix in {'.cpp','.h'}:p.write_text(re.sub(r'\b_B\b','ZZ_ARM_BRANCH_B',p.read_text()))
# IMM32 rotates 32-bit bit patterns; signed constant shifts are undefined C++.
# Keep the upstream encoding choices but perform their shifts as uae_u32.
codegen=port/'codegen_arm.h';encoding=codegen.read_text()
begin=encoding.index('#define IMM32(c)');end=encoding.index('\n\n',begin)
macro=encoding[begin:end].replace('((c)', '((uae_u32)(c)')
codegen.write_text(encoding[:begin]+macro+encoding[end:])
obj=port/'compemu_support.o'
r=subprocess.run([*RUN,'arm-none-eabi-g++','-I'+inside(port),*flags,'-c',inside(port/'compemu_support.cpp'),'-o',inside(obj)],capture_output=True,text=True)
(port/'compile.log').write_text(r.stdout+r.stderr)
audit=dict(compiled=r.returncode==0,executable=False,required_hooks=['zzuae_jit_alloc_executable','zzuae_jit_free_executable','zzuae_jit_publish_code'])
if r.returncode:print('\n'.join(r.stderr.splitlines()[:20]),flush=True)
else:
    symbols=subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm','--undefined-only',str(obj)],text=True)
    (port/'undefined.txt').write_text(symbols)
    assert all(name in symbols for name in audit['required_hooks'])
    print('COMPILED platform audit; executable memory/cache hooks intentionally unresolved',flush=True)
(dest/'platform-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
# Optional relocatable link against the implemented cache hooks. This still
# lacks CPU dispatch/FP context integration and must never be run as a player.
import sys
if '--cache-hooks' in sys.argv:
    hooks=OUT/'machine-jit_cache.o'
    if not hooks.exists():raise SystemExit('Build --jit-cache-test first')
    # Upstream defaults to a 16 MiB cache, which does not fit this port's owned
    # budget. Keep the experiment to 512 KiB plus its dispatch stubs.
    header=(OUT/'src/include/newcpu.h').read_text()
    assert '#define MAX_JIT_CACHE 16384' in header
    (port/'newcpu.h').write_text(header.replace('#define MAX_JIT_CACHE 16384','#define MAX_JIT_CACHE 512'))
    link_objects=[]
    for name in ['compemu','compstbl','compemu_support']:
        obj=port/(name+'-bounded.o')
        subprocess.run([*RUN,'arm-none-eabi-g++','-I'+inside(port),*flags,'-c',inside(port/(name+'.cpp')),'-o',inside(obj)],check=True,stdout=subprocess.DEVNULL)
        link_objects.append(obj)
    joined=port/'cache-hooks-linked.o'
    subprocess.run(['/opt/homebrew/opt/lld/bin/ld.lld','-r',*map(str,link_objects),str(hooks),'-o',str(joined)],check=True)
    symbols=subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm','--undefined-only',str(joined)],text=True)
    assert not any(n in symbols for n in audit['required_hooks'])
    (port/'cache-hooks-undefined.txt').write_text(symbols)
    (dest/'cache-hooks-link.json').write_text(json.dumps(dict(upstream=PIN,cache_kib=512,hooks_resolved=True,executable=False,guest_jit=False,remaining_symbols=symbols.splitlines()),indent=2)+'\n')
    print('PASS relocatable JIT components/cache-hooks link; no runnable guest JIT',flush=True)
