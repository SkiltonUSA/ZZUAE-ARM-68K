#!/usr/bin/env python3
"""Relocated Cortex-A9 instruction model; does not prove hardware/cache behavior."""
from pathlib import Path
import sys,struct,subprocess
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from build_zz9000_debug import unpack_elf
out=ROOT/'.context/amiga/uae4arm';block=0x800000
image,rel,_=unpack_elf((out/'uae-probe.elf').read_bytes(),0x100000)
symbols={p[2]:int(p[0],16) for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',out/'uae-probe.elf'],text=True).splitlines() if len(p:=line.split())==3}
for base in [0x12000040,0x13805040]:
 data=bytearray(image)
 for offset in rel:struct.pack_into('<I',data,offset,struct.unpack_from('<I',data,offset)[0]+base)
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
 u.mem_map(base&~4095,block+8192);u.mem_write(base,bytes(data))
 # Independent callback stubs: stop=false, clock=constant. No MMIO/cache model.
 u.mem_write(base+0x70000,bytes.fromhex('0000a0e31eff2fe1'))
 u.mem_write(base+0x70010,bytes.fromhex('0100a0e31eff2fe1'))
 def access(u,kind,address,size,value,user):
  if size>1 and address%size:raise AssertionError(f'unaligned {address:x} size={size}')
 u.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,access)
 def call(stop):
  u.reg_write(UC_ARM_REG_SP,base+block-4112);u.reg_write(UC_ARM_REG_LR,base+0x71000)
  for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],[1,base+0x72000,base+stop,base+0x70000]):u.reg_write(r,v)
  u.emu_start(base+symbols['mesen_test'],base+0x71000,count=20000000)
  assert u.reg_read(UC_ARM_REG_PC)==base+0x71000
  return u.reg_read(UC_ARM_REG_R0),struct.unpack('<11I',u.mem_read(base+0x72000,44))
 rc,result=call(0x70000)
 assert rc==0 and result[:6]==(26000,0,234000,11000,0,0),(rc,result)
 assert call(0x70010)[0]==2
 print(f'PASS base={base:08x}: 26,000 instructions, 234,000 guest cycles; memory/register/flags and cancellation checks')
