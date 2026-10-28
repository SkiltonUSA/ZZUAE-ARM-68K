#!/usr/bin/env python3
"""Execute upstream A32 bitfield encodings at all valid bit ranges on an A9."""
import argparse,struct,subprocess,tempfile
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-dir',type=Path,required=True);a=p.parse_args()
header=(a.source_dir/'codegen_arm.h').read_text()
names=['CC_BFI_rrii','BFI_rrii','CC_BFC_rii','BFC_rii','CC_UBFX_rrii','UBFX_rrii']
macros='\n'.join(next(line for line in header.splitlines()if line.startswith('#define '+name+'('))for name in names)
with tempfile.TemporaryDirectory()as folder:
 d=Path(folder);source=d/'emit.cpp';binary=d/'emit'
 source.write_text('''#include <cstdint>
#include <cstdio>
#define NATIVE_CC_AL 14u
uint32_t word;
#define _W(value) (word=(value))
'''+macros+'''
int main(){
 unsigned pairs[][2]={{0,1},{1,1},{12,14}};
 for(unsigned op=0;op<3;op++)for(unsigned lo=0;lo<32;lo++)for(unsigned hi=lo;hi<32;hi++)for(auto &pair:pairs){
  unsigned dst=pair[0],src=pair[1];
  if(op==0)BFI_rrii(dst,src,lo,hi);
  if(op==1)BFC_rii(dst,lo,hi);
  if(op==2)UBFX_rrii(dst,src,lo,hi-lo+1);
  uint32_t row[]={op,lo,hi,dst,src,word};fwrite(row,sizeof(row),1,stdout);
 }
}
''')
 subprocess.run(['clang++','-std=c++11','-fsanitize=undefined',str(source),'-o',str(binary)],check=True)
 rows=list(struct.iter_unpack('<6I',subprocess.check_output([str(binary)])))
registers=[UC_ARM_REG_R0+i for i in range(13)]+[UC_ARM_REG_SP,UC_ARM_REG_LR]
for address in [0x100000,0x1fff000]:
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9);u.mem_map(address,4096)
 checks=0
 for op,lo,hi,dst,src,word in rows:
  u.mem_write(address,struct.pack('<I',word));u.ctl_remove_cache(address,address+4)
  for seed in [0,0xffffffff,0x80000000,0x12345678,0xabcdef01]:
   initial=[(seed^(0x13579000*i))&0xffffffff for i in range(15)]
   for n,v in enumerate(initial):u.reg_write(registers[n],v)
   u.reg_write(UC_ARM_REG_CPSR,0xa8000013)
   u.emu_start(address,address+4,count=1)
   field=(1<<(hi-lo+1))-1;mask=field<<lo
   expected=((initial[dst]&~mask)|((initial[src]&field)<<lo))if op==0 else (initial[dst]&~mask)if op==1 else (initial[src]>>lo)&field
   for n,v in enumerate(initial):assert u.reg_read(registers[n])==(expected if n==dst else v),(op,lo,hi,dst,src,n)
   assert u.reg_read(UC_ARM_REG_CPSR)==0xa8000013
   checks+=1
 print('PASS BFI/BFC/UBFX:',checks,'cases, all bit ranges, aliases and flags at',hex(address))
