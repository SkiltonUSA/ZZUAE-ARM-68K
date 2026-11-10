from pathlib import Path
import subprocess,sys,random,struct
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *

p=Path(__file__).resolve().parent
sys.path.insert(0,'scripts')
import build_uae4arm as b
subprocess.run([*b.RUN,'arm-none-eabi-gcc','-mcpu=cortex-a9','-c',b.inside(p/'kernel.S'),'-o',b.inside(p/'kernel.o')],check=True)
subprocess.run(['/opt/homebrew/opt/llvm/bin/llvm-objcopy','-O','binary','--only-section=.text',str(p/'kernel.o'),str(p/'kernel.bin')],check=True)
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
u.mem_map(0x10000,0x10000);u.mem_write(0x10000,(p/'kernel.bin').read_bytes())
u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
rng=random.Random(40821)
count=0
for scale in range(3):
 for number in range(8):
  for alignment in range(8):
   for data in [0,1,3,0xc0000000,0xffffffff,0xaaaaaaaa,0x55555555]+[rng.getrandbits(32) for _ in range(48)]:
    initial=[rng.getrandbits(16) for _ in range(96)]
    expected=initial[:];start=8+alignment
    for i in range(16):
     color=((data>>(2*i))&3)<<(2*number)
     for j in range(1<<scale):expected[start+(i<<scale)+j]|=color
    u.mem_write(0x18000,struct.pack('<96H',*initial))
    dregs=[rng.getrandbits(64) for _ in range(32)]
    for i,value in enumerate(dregs):u.reg_write(UC_ARM_REG_D0+i,value)
    fpscr=0x09000000;u.reg_write(UC_ARM_REG_FPSCR,fpscr)
    saved={r:rng.getrandbits(32) for r in range(UC_ARM_REG_R4,UC_ARM_REG_R11+1)}
    for r,value in saved.items():u.reg_write(r,value)
    for r,value in [(UC_ARM_REG_R0,0x18000+2*start),(UC_ARM_REG_R1,data),(UC_ARM_REG_R2,2*number),(UC_ARM_REG_R3,scale),
                    (UC_ARM_REG_SP,0x1f000),(UC_ARM_REG_LR,0x11000)]:u.reg_write(r,value)
    u.emu_start(0x10000,0x11000,count=1000)
    assert u.reg_read(UC_ARM_REG_PC)==0x11000
    assert list(struct.unpack('<96H',u.mem_read(0x18000,192)))==expected,(scale,number,alignment,hex(data))
    assert u.reg_read(UC_ARM_REG_SP)==0x1f000
    assert all(u.reg_read(r)==v for r,v in saved.items())
    assert all(u.reg_read(UC_ARM_REG_D0+i)==v for i,v in enumerate(dregs))
    assert u.reg_read(UC_ARM_REG_FPSCR)==fpscr
    assert u.reg_read(UC_ARM_REG_FPEXC)==0x40000000
    count+=1
print('PASS',count,'actual ARM NEON OR cases; guards, alignment, 1x/2x/4x, integer/SIMD/FPSCR state preserved')
