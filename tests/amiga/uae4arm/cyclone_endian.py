#!/usr/bin/env python3
"""Execute all 65536 opcode encodings through both Cyclone fetch layouts.

Tests our endian adaptation against pinned upstream Cyclone, not against real
68000 hardware. Register, status, cycles, faults and full data RAM must match.
"""
import json,struct,subprocess,sys,time
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from build_zz9000_debug import unpack_elf
BASE=0x12000040;RETURN=BASE+0x700000
class Core:
 def __init__(self,be):
  self.be=be
  elf=ROOT/'.context/amiga/uae4arm'/('cyclone-probe-be' if be else 'cyclone-probe')/'step.elf'
  data,rel,_=unpack_elf(elf.read_bytes(),0x100000)
  for at in rel:struct.pack_into('<I',data,at,struct.unpack_from('<I',data,at)[0]+BASE)
  self.sym={p[2]:int(p[0],16)+BASE for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',elf],text=True).splitlines()if len(p:=line.split())==3}
  self.u=Uc(UC_ARCH_ARM,UC_MODE_ARM);self.u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
  self.u.mem_map(BASE&~4095,0x802000);self.u.mem_write(BASE,bytes(data));self.call('CycloneInitJT',self.sym['CycloneJumpTab'])
  # Keep the same context-to-RAM offset: the upstream MOVEM odd-address
  # exception path leaks that displacement into the stacked PC. This test
  # checks our endian adaptation, not upstream exception correctness.
  self.ram=self.sym['_ZL3ram'];self.ctx=self.ram+0x100000
 def call(self,name,*args):
  u=self.u;u.reg_write(UC_ARM_REG_SP,BASE+0x7f0000);u.reg_write(UC_ARM_REG_LR,RETURN)
  for reg,val in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3),args):u.reg_write(reg,val)
  u.emu_start(self.sym[name],RETURN,count=1000000 if name=='CycloneInitJT' else 20000)
  assert u.reg_read(UC_ARM_REG_PC)==RETURN,(name,hex(u.reg_read(UC_ARM_REG_PC)))
  return u.reg_read(UC_ARM_REG_R0)
 def step(self,op,seed,odd_address=False):
  ram=bytearray(65536)
  for i in range(0,256,4):struct.pack_into('>I',ram,i,0x200) # exception vectors
  struct.pack_into('>8H',ram,0x100,op,seed,0x4000,0,0x4100,0x4e71,0x4e71,0x4e71)
  struct.pack_into('>2H',ram,0x200,0x4e71,0x60fe)
  for i in range(0x4000,0x4900):ram[i]=(i*13+seed)&255
  if not self.be:ram[::2],ram[1::2]=ram[1::2],ram[::2]
  self.u.mem_write(self.ram,bytes(ram));self.u.mem_write(self.sym['_ZL6faults'],bytes(4))
  context=bytearray(0xb0)
  for i in range(8):struct.pack_into('<I',context,i*4,(0x10203040*(i+1)+seed)&0xffffffff);struct.pack_into('<I',context,32+i*4,0x4000+i*256)
  if odd_address:struct.pack_into('<I',context,32,0x4001)
  struct.pack_into('<I',context,0x40,self.ram+0x100);struct.pack_into('<I',context,0x48,0x4800)
  struct.pack_into('<I',context,0x54,self.sym['CycloneJumpTab']);struct.pack_into('<I',context,0x60,self.ram)
  names=['_ZL7checkpcj','_ZL5read8j','_ZL6read16j','_ZL6read32j','_ZL6write8jh','_ZL7write16jt','_ZL7write32jj','_ZL5read8j','_ZL6read16j','_ZL6read32j','_ZL3irqi','_ZL5resetv']
  for i,n in enumerate(names):struct.pack_into('<I',context,0x64+i*4,self.sym[n])
  self.u.mem_write(self.ctx,bytes(context));self.call('CycloneSetSr',self.ctx,0x2700|(seed&31));self.call('CycloneRun',self.ctx)
  result=bytes(self.u.mem_read(self.ctx,64))
  pc=struct.unpack('<I',self.u.mem_read(self.ctx+0x40,4))[0]-self.ram
  result+=struct.pack('<I',pc&0xffffffff)+struct.pack('<I',self.call('CycloneGetSr',self.ctx))
  result+=bytes(self.u.mem_read(self.ctx+0x48,4))+bytes(self.u.mem_read(self.ctx+0x58,8))+bytes(self.u.mem_read(self.sym['_ZL6faults'],4))
  ram=bytearray(self.u.mem_read(self.ram,65536))
  if not self.be:ram[::2],ram[1::2]=ram[1::2],ram[::2]
  return result,ram
if __name__=='__main__':
 a,b=Core(False),Core(True);start=time.monotonic();bad=[]
 for op in range(65536):
  seed=(op*73+0x9235)&65535
  x,y=a.step(op,seed),b.step(op,seed)
  if x!=y:
   bad.append({'opcode':f'{op:04x}','seed':seed,'context_a':x[0].hex(),'context_b':y[0].hex(),'memory_diff':sum(p!=q for p,q in zip(x[1],y[1]))})
   if len(bad)==10:break
  if op%8192==0:print(f'checked {op} encodings',flush=True)
 print(json.dumps({'checked':op+1,'failures':bad,'seconds':round(time.monotonic()-start,2)},indent=2))
 assert not bad
