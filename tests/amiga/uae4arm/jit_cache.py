#!/usr/bin/env python3
"""Execute cache hooks and generated ARM witnesses; cache coherence needs hardware."""
import struct,subprocess,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'amiga/uae4arm'))
from elf import unpack
elf=Path(sys.argv[1]) if len(sys.argv)>1 else root/'.context/amiga/uae4arm/uae-machine.elf'
for base in [0x12000040,0x14000fc0]:
 size=0x2000000;image,rel,_=unpack(elf.read_bytes())
 for off in rel:struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+base)
 sym={a[2]:int(a[0],16)+base for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',elf],text=True).splitlines() if len(a:=line.split())==3}
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
 u.mem_map(base&~4095,size+8192);u.mem_write(base,bytes(image))
 u.mem_write(sym['uae_shared'],struct.pack('<I',base))
 table=(base+0x400000+16383)&~16383;l2=table+16384
 for index,section in enumerate(range(base>>20,(base+size-1>>20)+1)):
  leaf=l2+index*1024;u.mem_write(table+section*4,struct.pack('<I',leaf|1))
  for n in range(256):u.mem_write(leaf+4*n,struct.pack('<I',(section<<20)+(n<<12)|0x117))
 before=bytes(u.mem_read(table,0x10000))
 end=base+size-256;sp=(base+size-8192)&~15
 aborted=[]
 def abort(uc,*args):aborted.append(True);uc.emu_stop()
 u.hook_add(UC_HOOK_CODE,abort,begin=sym['abort'],end=sym['abort'])
 def call(name,*args):
  aborted.clear();u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,end)
  for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1],args):u.reg_write(reg,value)
  u.emu_start(sym[name],end,count=1000000)
  assert aborted or u.reg_read(UC_ARM_REG_PC)==end,name
  return u.reg_read(UC_ARM_REG_R0)
 assert call('zzuae_jit_cache_selftest')==0 and not aborted
 assert struct.unpack('>4I',u.mem_read(base+0x482a00,16))==(0x4a495443,48,48,1)
 assert bytes(u.mem_read(table,0x10000))==before,'page descriptors not restored'
 p=call('zzuae_jit_alloc_executable',4096);assert p and not p%4096
 for start,stop in [(p-4,p+4),(p,p+4097),(p,p),(p+8,p),(0xfffffff0,16)]:
  call('zzuae_jit_publish_code',start,stop);assert aborted,'invalid publication accepted'
 call('zzuae_jit_free_executable',p+4,4096);assert aborted
 call('zzuae_jit_free_executable',p,4095);assert aborted
 call('zzuae_jit_free_executable',p,4096);assert not aborted
 assert bytes(u.mem_read(table,0x10000))==before
 call('zzuae_jit_free_executable',p,4096);assert aborted
 p=call('zzuae_jit_alloc_executable',0x100000);assert p and not aborted
 call('zzuae_jit_free_executable',p,0x100000);assert not aborted
 assert bytes(u.mem_read(table,0x10000))==before
 # A bad second descriptor must fail before even the first page becomes executable.
 desc=struct.unpack('<I',u.mem_read(table+((p+4096)>>20)*4,4))[0]
 where=(desc&~1023)+(((p+4096)>>12)&255)*4
 u.mem_write(where,struct.pack('<I',0))
 broken=bytes(u.mem_read(table,0x10000))
 call('zzuae_jit_alloc_executable',8192);assert aborted
 assert bytes(u.mem_read(table,0x10000))==broken
 print('PASS ARM cache hooks: owned allocation, 48 generated/rewritten calls, line/page crossing, release/reallocate, restored XN, invalid spans/frees rejected; base',hex(base))
