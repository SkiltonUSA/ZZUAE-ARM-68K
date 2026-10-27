#!/usr/bin/env python3
"""Execute bitplane assembly against a pixel oracle, including state/guards."""
import random, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import *
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
u.mem_map(0x10000,0x10000);u.mem_write(0x10000,Path(sys.argv[1]).read_bytes())
u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
regs=[UC_ARM_REG_D0+i for i in range(32)]+[UC_ARM_REG_R4+i for i in range(8)]
values=[0x123456789abcdef0^(i*0x1001001001001) for i in range(32)]+[0x1000+i for i in range(8)]
rng=random.Random(431);src=0x14004;dst=0x15004;sp=0x1e000;end=0x1f000
for planes in range(2,7):
 for words in range(51):
  raw=bytes(rng.randrange(256) for _ in range(1600))
  expected=bytes(sum(((struct.unpack_from('<I',raw,p*200+(x//32)*4)[0]>>(31-x%32))&1)<<p for p in range(planes)) for x in range(words*32))
  u.mem_write(src,raw);u.mem_write(dst-4,b'\xa5'*(1600+8))
  for reg,value in zip(regs,values):u.reg_write(reg,value)
  u.reg_write(UC_ARM_REG_FPSCR,0x01000000)
  for reg,value in [(UC_ARM_REG_R0,dst),(UC_ARM_REG_R1,words),(UC_ARM_REG_R2,src),(UC_ARM_REG_R3,planes),(UC_ARM_REG_SP,sp),(UC_ARM_REG_LR,end)]:u.reg_write(reg,value)
  u.emu_start(0x10000,end,count=100000)
  assert u.reg_read(UC_ARM_REG_PC)==end and u.reg_read(UC_ARM_REG_SP)==sp
  assert bytes(u.mem_read(dst,words*32))==expected,(planes,words)
  assert bytes(u.mem_read(dst-4,4))==b'\xa5'*4
  assert bytes(u.mem_read(dst+words*32,1604-words*32))==b'\xa5'*(1604-words*32)
  assert bytes(u.mem_read(src,1600))==raw
  assert [u.reg_read(r) for r in regs]==values,'Register leak'
  assert u.reg_read(UC_ARM_REG_FPSCR)==0x01000000
print('PASS bitplanes: planes 2–6, wordcounts 0–50, pixel oracle, guards, source, D0–D31/FPSCR/callee state')
