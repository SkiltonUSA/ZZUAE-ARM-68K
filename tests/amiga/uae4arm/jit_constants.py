#!/usr/bin/env python3
"""Execute the real emitter's LOAD_U32 output on the A9 instruction model."""
from pathlib import Path
import argparse,struct,subprocess,tempfile,sys,re
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_READ
from unicorn.arm_const import *
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source-dir',type=Path,required=True)
p.add_argument('--prepare',action='store_true')
a=p.parse_args()
source=(a.source_dir/'codegen_arm.cpp').read_text()
header=(a.source_dir/'codegen_arm.h').read_text()
if a.prepare:
 sys.path.insert(0,str(Path.cwd()/'scripts'))
 from prepare_uae4arm_jit_constants import movw_constants
 original=source
 source,header=movw_constants(source,header)
 # This switch must preserve every neighbouring emitter routine.
 pattern=r'STATIC_INLINE void LOAD_U32\([^}]+\n}'
 assert re.sub(pattern,'',source)==re.sub(pattern,'',original),'unrelated emitter code changed'
start=source.index('STATIC_INLINE void LOAD_U32(')
function=source[start:source.index('\n}',start)+2]
# Use the pinned emitter's actual instruction encodings, not a second encoder.
names=['CC_MOVW_ri16','MOVW_ri16','CC_MOVT_ri16','MOVT_ri16']
macros='\n'.join(next(line for line in header.splitlines() if line.startswith('#define '+name+'(')) for name in names)
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);cpp=d/'emit.cpp';binary=d/'emit'
 cpp.write_text('''#include <cstdint>
#include <cstdio>
#include <cassert>
using uae_u32=uint32_t;using uae_s32=int32_t;
#define STATIC_INLINE static inline
#define NATIVE_CC_AL 14u
static uint32_t words[4],used,literals;
#define _W(value) (words[used++]=(value))
static int data_long_offs(uint32_t){++literals;return 0;}
#define RPC_INDEX 15
#define LDR_rRI(r,base,offset) _W(0xe59f0000u|((r)<<12))
'''+macros+'\n'+function+r'''
int main(){
 uint32_t values[]={0,1,0xffff,0x10000,0xffffffff,0x80000000,0x3ff,0xdeadbeef,0x101f0040,0x14000fc0};
 uint32_t rng=0x12345678;
 for(uint32_t reg=0;reg<15;reg++)for(uint32_t n=0;n<522;n++){
  rng=rng*1664525u+1013904223u;uint32_t v=n<10?values[n]:rng;
  used=literals=0;LOAD_U32(reg,v);
  assert(literals==0 && "LOAD_U32 still uses a literal pool");
  assert(used==(v>>16?2u:1u));
  uint32_t row[]={reg,v,used,words[0],used==2?words[1]:0};
  fwrite(row,sizeof(row),1,stdout);
 }
}
''')
 subprocess.run(['clang++','-std=c++11','-fsanitize=undefined',str(cpp),'-o',str(binary)],check=True)
 output=subprocess.check_output([str(binary)])
rows=list(struct.iter_unpack('<5I',output));assert len(rows)==15*522
registers=[UC_ARM_REG_R0+i for i in range(13)]+[UC_ARM_REG_SP,UC_ARM_REG_LR]
for address in [0x100000,0x1fff000]:
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9);u.mem_map(address,4096)
 reads=[];u.hook_add(UC_HOOK_MEM_READ,lambda *args:reads.append(1))
 for reg,value,count,first,second in rows:
  u.mem_write(address,struct.pack('<2I',first,second));u.ctl_remove_cache(address,address+8)
  initial=[0x13579000+i for i in range(15)]
  for n,v in enumerate(initial):u.reg_write(registers[n],v)
  u.reg_write(UC_ARM_REG_CPSR,0xa8000013)
  u.emu_start(address,address+count*4,count=3)
  for n,v in enumerate(initial):assert u.reg_read(registers[n])==(value if n==reg else v),(reg,value,n)
  assert u.reg_read(UC_ARM_REG_CPSR)==0xa8000013
 assert not reads,'constant construction performed data reads'
 print('PASS LOAD_U32:',len(rows),'constants/register cases, preserved registers/flags, no data reads at',hex(address))
