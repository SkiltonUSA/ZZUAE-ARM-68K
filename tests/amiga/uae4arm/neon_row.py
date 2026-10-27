#!/usr/bin/env python3
"""Execute the optional ARM leaf in Unicorn. No physical timing claim."""
import struct,subprocess,sys
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/'amiga/uae4arm'))
from elf import unpack
elf=Path(sys.argv[1]) if len(sys.argv)>1 else root/'.context/amiga/uae4arm/uae-machine.elf'
base=0x12000040;size=0x2000000
image,rel,_=unpack(elf.read_bytes())
for off in rel:struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+base)
sym={a[2]:int(a[0],16)+base for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',elf],text=True).splitlines() if len(a:=line.split())==3}
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
u.mem_map(base&~4095,size+8192);u.mem_write(base,bytes(image))
end=base+size-0x100;sp=(base+size-0x1000)&~15
def call(name,*args):
    u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,end)
    for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args):u.reg_write(reg,value)
    u.emu_start(sym[name],end,count=100000)
    assert u.reg_read(UC_ARM_REG_PC)==end,name
    assert u.reg_read(UC_ARM_REG_SP)==sp
    return u.reg_read(UC_ARM_REG_R0)
# Unicorn's A9 CPACR MRC returns zero despite its configurable register.
# Correct only that read, as in the DOSBox model. Feature instructions execute.
def cpacr(uc,address,*args):
    uc.reg_write(UC_ARM_REG_R1,uc.reg_read(UC_ARM_REG_C1_C0_2));uc.reg_write(UC_ARM_REG_PC,address+4)
u.hook_add(UC_HOOK_CODE,cpacr,begin=sym['zu_neon_available'],end=sym['zu_neon_available'])
for policy,enabled,wanted in [(0,0,0),(0xf00000,0,0),(0xf00000,0x40000000,1),(0x80f00000,0x40000000,0)]:
    u.reg_write(UC_ARM_REG_C1_C0_2,policy);u.ctl_flush_tb();u.reg_write(UC_ARM_REG_FPEXC,enabled)
    assert call('zu_neon_available')==wanted
    assert u.reg_read(UC_ARM_REG_C1_C0_2)==policy and u.reg_read(UC_ARM_REG_FPEXC)==enabled
u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.ctl_flush_tb();u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
registers=[UC_ARM_REG_D0+i for i in range(32)]+[UC_ARM_REG_R4+i for i in range(8)]
values=[0x123456789abcdef0^(i*0x1001001001001) for i in range(32)]+[0x1000+i for i in range(8)]
for reg,value in zip(registers,values):u.reg_write(reg,value)
u.reg_write(UC_ARM_REG_FPSCR,0x01000000)
src=base+0x1900000+2;dst=base+0x1910000+4
for start in range(0,65536,640):
    colors=[(start+x)&65535 for x in range(640)]
    raw=struct.pack('<640H',*colors);u.mem_write(src,raw)
    for fmt in [3,4]:
        for level in [0,4,5,6,8]:
            u.mem_write(dst-4,b'\xa5'*(640*4+8))
            call('zu_convert_neon',dst,src,fmt,level)
            expected=bytearray()
            for c in colors:
                r,g,b=c>>11,(c>>5)&63,c&31
                r=(r<<3)|(r>>2);g=(g<<2)|(g>>4);b=(b<<3)|(b>>2)
                expected.extend(v*level//8 for v in ([b,g,r,255] if fmt==3 else [255,r,g,b]))
            assert bytes(u.mem_read(dst,2560))==expected,(start,fmt,level)
            assert bytes(u.mem_read(dst-4,4))==b'\xa5'*4 and bytes(u.mem_read(dst+2560,4))==b'\xa5'*4
            assert bytes(u.mem_read(src,1280))==raw
            assert [u.reg_read(r) for r in registers]==values,'Register leak'
            assert u.reg_read(UC_ARM_REG_FPSCR)==0x01000000
print('PASS ARM NEON: RGB565 colour space, both formats, all brightness levels, unaligned-to-16 buffers, guards, source unchanged, D0-D31/FPSCR/integer callee state and feature-policy fallback')
