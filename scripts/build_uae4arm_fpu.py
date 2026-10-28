#!/usr/bin/env python3
"""Build optional native-VFP guest FPU against the already-built JIT core ABI."""
import hashlib,json,runpy,shutil,subprocess,sys
from pathlib import Path
from uae4arm_version import VERSION
import build_uae4arm as b
ROOT=b.ROOT; BASE=Path(sys.argv[sys.argv.index('--base')+1]).resolve() if '--base' in sys.argv else b.OUT/'jit-execution'
OUT=b.OUT/'fpu-execution';SRC=b.SRC
record=json.loads((BASE/'build-manifest.json').read_text())
assert record['guest_jit'] and record['upstream']['upstream']==b.PIN
assert record['version']==VERSION,'FPU base must match the product version'
OUT.mkdir(parents=True,exist_ok=True)
for name in ['compile.json','libgcc.a','mapping.elf']:
 shutil.copy2(BASE/name,OUT/name)
for p in BASE.glob('*.o'):shutil.copy2(p,OUT/p.name)
# No struct/ABI change: retain the recorded core compiler flags and includes.
flags=json.loads((OUT/'compile.json').read_text())['flags']
source=BASE/'src/newcpu.cpp';s=source.read_text().replace('/* No guest FPU in the 68000 profile. */','fpu_reset ();')
(OUT/'newcpu-fpu.cpp').write_text(s)
subprocess.run([*b.RUN,'arm-none-eabi-g++',*flags,'-c',b.inside(OUT/'newcpu-fpu.cpp'),'-o',b.inside(OUT/'newcpu.o')],check=True)
s=(b.UP/'src/fpp.cpp').read_text().replace('#include "fpp_native.cpp"','#include "fpu_native.inc"\n#include "fpp_native.cpp"')
s=s.replace('static void fpsr_set_exception(uae_u32 exception);','unsigned zz_fpu_instructions,zz_fpu_data_ops,zz_fpu_saves,zz_fpu_restores;\nstatic void fpsr_set_exception(uae_u32 exception);')
for name in ['arithmetic','bcc','scc','dbcc','trapcc','save','restore']:
 a=s.index('void fpuop_'+name+' (');a=s.index('{',a);s=s[:a+1]+'\n ++zz_fpu_instructions;'+s[a+1:]
for name,counter in [('fp_arithmetic(fpdata *src, fpdata *dst, int extra)\n{','data_ops'),('fpuop_save (uae_u32 opcode)\n{','saves'),('fpuop_restore (uae_u32 opcode)\n{','restores')]:
 assert s.count(name)==1,name
 s=s.replace(name,name+'\n ++zz_fpu_'+counter+';')
(OUT/'fpp.cpp').write_text(s)
fpflags=[x.replace('-mfloat-abi=soft','-mfloat-abi=softfp') for x in flags]+['-mfpu=vfpv3','-frounding-math','-I'+b.inside(b.UP/'src')]
subprocess.run([*b.RUN,'arm-none-eabi-g++',*fpflags,'-c',b.inside(OUT/'fpp.cpp'),'-o',b.inside(OUT/'fpp.o')],check=True)
# Assemble the same guest instruction fixture for model and physical MB_VERIFY.
from amiga import PIN
cross=['podman','--connection','nuflix-converter-root','run','--rm','--platform','linux/amd64','-v',str(ROOT)+':/work','-w','/work',PIN['image']]
obj=OUT/'fpu_guest.o';raw=OUT/'fpu_guest.bin'
subprocess.run([*cross,'m68k-amigaos-gcc','-m68020','-m68881','-c','tests/amiga/uae4arm/fpu_guest.S','-o',b.inside(obj)],check=True)
subprocess.run([*cross,'m68k-amigaos-objcopy','-O','binary',b.inside(obj),b.inside(raw)],check=True)
(OUT/'fpu_fixture.h').write_text('static const unsigned char zu_fpu_fixture[]={'+','.join(map(str,raw.read_bytes()))+'};\n')
b.OUT=OUT;b.prepare=lambda:BASE/'src'
sys.argv=['build_uae4arm_machine.py','--guest-jit','--guest-fpu']+(['--hardware'] if '--hardware' in sys.argv else [])
runpy.run_path(str(ROOT/'scripts/build_uae4arm_machine.py'),run_name='__main__')
