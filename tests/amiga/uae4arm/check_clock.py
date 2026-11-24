from pathlib import Path
import sys,struct,subprocess
from unicorn import *
from unicorn.arm_const import *
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'amiga/uae4arm'));from elf import unpack
elf=Path(sys.argv[1]);base=0x12000040
payload,rel,_=unpack(elf.read_bytes(),allocation_size=0x4800000)
for at in rel:struct.pack_into('<I',payload,at,struct.unpack_from('<I',payload,at)[0]+base)
sym={p[2]:int(p[0],16)+base for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',elf],text=True).splitlines() if len(p:=line.split())==3}
for divisor in [333,400]:
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
 u.mem_map(base&~4095,0x4802000);u.mem_write(base,bytes(payload));u.mem_map(0xf8f00000,4096)
 u.mem_write(sym['uae_shared'],struct.pack('<I',base));u.mem_write(base+0x482890,struct.pack('>I',divisor))
 for ticks in [0,divisor*1000000,(1<<32)-1,1<<32,divisor*86400*1000000]:
  u.mem_write(0xf8f00200,struct.pack('<Q',ticks));u.reg_write(UC_ARM_REG_SP,base+0x47ff000);u.reg_write(UC_ARM_REG_LR,base+0x480100)
  u.emu_start(sym['_Z14zzuae_clock_usv'],base+0x480100,count=100000)
  result=u.reg_read(UC_ARM_REG_R0)|(u.reg_read(UC_ARM_REG_R1)<<32)
  assert result==ticks//divisor,(divisor,ticks,result,ticks//divisor)
 print('PASS ARM clock',divisor,'ticks/us: second, timer rollover and 24-hour uptime')
