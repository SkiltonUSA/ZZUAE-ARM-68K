#!/usr/bin/env python3
"""Run actual translated guest blocks in the A9 instruction model, VFP disabled."""
import struct,subprocess,sys,time
from pathlib import Path
from unicorn import *
from unicorn.arm_const import *
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'amiga/uae4arm'))
from elf import unpack
elf=root/'.context/amiga/uae4arm/jit-execution/guest.elf'
mmu='--mmu' in sys.argv
fault='--fault' in sys.argv
cancel='--cancel' in sys.argv
for base in [0x101f0040,0x12000040,0x14000fc0]:
 image,rel,_=unpack(elf.read_bytes());size=0x2000000
 for off in rel:struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+base)
 sym={a[2]:int(a[0],16)+base for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',elf],text=True).splitlines() if len(a:=line.split())==3}
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
 u.mem_map(base&~4095,size+8192);u.mem_write(base,bytes(image))
 u.mem_write(sym['uae_shared'],struct.pack('<I',base))
 table=(base+0x400000+16383)&~16383;l2=table+16384
 for index,section in enumerate(range(base>>20,(base+size-1>>20)+1)):
  leaf=l2+index*1024;u.mem_write(table+section*4,struct.pack('<I',leaf|1))
  for n in range(256):
   page=(section<<20)+(n<<12);attr=0x117
   if mmu:
    attr=0x116 if page<base+0x400000 else 0x117
    if page<base or page+4096>base+size or (page<base+0x420000 and page+4096>base+0x400000) or (page<base+0x640000 and page+4096>base+0x480000):attr=(attr&1)|0x452
   u.mem_write(leaf+4*n,struct.pack('<I',page|attr))
 before=bytes(u.mem_read(table,0x10000))
 # Private guest flags use LDREX/STREX; never place them on the shared boundary page.
 assert (sym['regs']&~4095)>=((base+0x640000+4095)&~4095)
 end=base+0x300100;callback=base+0x300000;result=base+0x480200
 u.mem_write(callback,bytes.fromhex(('0100a0e3' if cancel else '0000a0e3')+'1eff2fe1'))
 u.mem_write(callback+16,bytes.fromhex('0000a0e31eff2fe1'))
 u.reg_write(UC_ARM_REG_SP,(base+size-8192)&~15);u.reg_write(UC_ARM_REG_LR,end)
 for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],[1,result,callback,callback+16]):u.reg_write(reg,value)
 arena=sym['_ZL5arena'];translated=[]
 def executed(uc,at,n,data):translated.append(at)
 u.hook_add(UC_HOOK_BLOCK,executed,begin=arena,end=arena+0x101000)
 def failed(uc,at,n,data):raise RuntimeError('fatal '+hex(at)+' LR '+hex(uc.reg_read(UC_ARM_REG_LR)))
 u.hook_add(UC_HOOK_CODE,failed,begin=sym['abort'],end=sym['abort'])
 if '--implicit-smc' in sys.argv:
  def skip_flush(uc,*args):uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
  u.hook_add(UC_HOOK_CODE,skip_flush,begin=sym['_Z12flush_icachei'],end=sym['_Z12flush_icachei'])
 if mmu:
  for crn,crm,opc2,value in [(2,0,0,table),(2,0,2,0),(3,0,0,1),(1,0,0,0x08c5187d)]:u.cpr_write(15,0,crn,crm,opc2,0,False,value)
 if fault:
  def inject(uc,at,n,data):
   if bytes(uc.mem_read(base+0x480940,4))!=b'\0\0\0\5':return
   prior=uc.reg_read(UC_ARM_REG_CPSR)
   vector=uc.cpr_read(15,0,12,0,0,0,False)
   uc.reg_write(UC_ARM_REG_CPSR,(prior&~31)|0x17)
   uc.reg_write(UC_ARM_REG_SPSR,prior)
   uc.reg_write(UC_ARM_REG_LR,at+8)
   uc.reg_write(UC_ARM_REG_PC,vector+16)
  u.hook_add(UC_HOOK_CODE,inject,begin=sym['_Z11map_overlayi'],end=sym['_Z11map_overlayi'])
 start=time.monotonic()
 try:u.emu_start(sym['mesen_test'],end,count=200000000)
 except Exception:
  print('PHASE',u.mem_read(base+0x480940,4).hex(),'PC',hex(u.reg_read(UC_ARM_REG_PC)),'LR',hex(u.reg_read(UC_ARM_REG_LR)),flush=True);raise
 values=struct.unpack('<11I',u.mem_read(result,44));print('RESULT',values,'generated blocks',len(translated),'seconds',round(time.monotonic()-start,2),flush=True)
 assert u.reg_read(UC_ARM_REG_PC)==end,'did not return'
 assert u.cpr_read(15,0,12,0,0,0,False)==0,'VBAR not restored'
 if fault:
  assert u.reg_read(UC_ARM_REG_R0)==1 and values[4]==104,values
  assert bytes(u.mem_read(base+0x482a40,8))==bytes.fromhex('4a464c5400000004')
  print('PASS injected data-abort landing, fatal unwind and VBAR restoration',hex(base));continue
 if cancel:
  assert u.reg_read(UC_ARM_REG_R0)==2 and values[0]==0 and values[4]==0,values
  assert bytes(u.mem_read(table,0x10000))==before,'cancel left executable pages'
  print('PASS cancellation, executable-page and VBAR restoration',hex(base));continue
 assert u.reg_read(UC_ARM_REG_R0)==0 and values[4]==0,values
 assert values[0]==240 and values[9]>0 and values[2]>0 and len(translated)>240,values
 assert bytes(u.mem_read(table,0x10000))==before,'page permissions not restored'
 print('PASS actual guest JIT vs interpreter, VFP disabled, restored executable pages; base',hex(base),flush=True)
