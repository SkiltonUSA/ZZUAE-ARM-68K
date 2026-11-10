from pathlib import Path
import runpy,sys,struct
core=Path('tests/amiga/uae4arm/check_machine.py').resolve();sys.path.insert(0,str(core.parent))
sys.argv=[str(core),'2','--elf','.context/amiga/uae4arm/a1200/gameplay/build-blitter-service/uae-machine.elf','--cache32','--engine','2','--profile','4','--synthetic-rom','--neon']
c=runpy.run_path(str(core));u=c['u'];sym=c['sym'];base=c['base'];block=c['block']
from unicorn.arm_const import *
u.mem_write(sym['timeframes'],struct.pack('<I',3000))
for i in range(1024):
 u.reg_write(UC_ARM_REG_SP,base+block-4112);u.reg_write(UC_ARM_REG_LR,base+0x480100)
 u.emu_start(sym['_Z9blitnastyv'],base+0x480100,count=10000)
 assert u.reg_read(UC_ARM_REG_PC)==base+0x480100
counts=struct.unpack('<6I',u.mem_read(sym['zu_profile_calls'],24));assert counts[0]>0 and counts[5]==counts[0],counts
print('PASS positive control: profiler records forced post-warmup calls',counts)
