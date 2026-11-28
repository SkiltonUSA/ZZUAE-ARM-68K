"""Drive real linked ARM media commands while withholding the frame ACK."""
import hashlib,struct
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
class DiskSwap:
 def __init__(self,u,sym,base):
  self.u,self.sym,self.base=u,sym,base;self.index=0;self.pending=False;self.reads=0;self.loaded={}
  self.cases=[(1,2,3,0),(1,0,2,2),(1,0,2,3),(1,1,1,2),(1,0,1,0),(2,0,1,0),
              (2,0,1,0), # not yet mounted: replacing a scheduled insertion remains safe
              (1,1,1,0),(2,1,1,0)]
  self.images=[bytes([x])*901120 for x in (0x35,0xa7)]
  self.expected={hashlib.sha256(x).hexdigest():i for i,x in enumerate(self.images)}
  def crc(uc,*args):
   if uc.reg_read(UC_ARM_REG_R1)!=901120:return
   digest=hashlib.sha256(uc.mem_read(uc.reg_read(UC_ARM_REG_R0),901120)).hexdigest()
   if digest in self.expected:
    frame=struct.unpack('<I',uc.mem_read(sym['timeframes'],4))[0]
    self.loaded[self.expected[digest]]=frame
  u.hook_add(UC_HOOK_CODE,crc,begin=sym['_Z9get_crc32Pvi'],end=sym['_Z9get_crc32Pvi'])
 def hold(self,frame):
  if frame!=1:return False
  self.reads+=1;assert self.reads<500,'ARM disk command did not acknowledge'
  at=self.base+0x483200
  if self.pending:
   reply,result=struct.unpack('>2I',self.u.mem_read(at+64,8))
   if reply!=self.index+1:return True
   assert result==self.cases[self.index][2],(self.index,result)
   self.index+=1;self.pending=False
  if self.index==len(self.cases):return False
  op,unit,expected,dma=self.cases[self.index]
  self.u.mem_write(self.sym['_ZL8dskdmaen'],struct.pack('<I',dma))
  self.u.mem_write(self.sym['_ZL8selected'],bytes([14 if dma else 15]))
  if op==2:
   where=self.base+0x560000 if unit==0 else self.sym['zzuae_disk1_image']
   self.u.mem_write(where,self.images[unit])
  self.u.mem_write(at,struct.pack('>3I',self.index+1,op,unit));self.pending=True
  return True
 def verify(self):
  assert self.index==len(self.cases)
  assert len(self.loaded)==2,self.loaded
  assert all(frame>=99 for frame in self.loaded.values()),self.loaded
  assert struct.unpack('>I',self.u.mem_read(self.base+0x483248,4))[0]==0x5a554d31
  print('PASS linked ARM disk swaps: bad unit, DMA read/write refusal, DF0 replacement, initially absent DF1, delayed insertion and both image CRC paths',self.loaded)
