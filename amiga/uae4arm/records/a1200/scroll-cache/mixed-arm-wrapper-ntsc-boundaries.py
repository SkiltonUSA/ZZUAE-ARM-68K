import sys
sys.path.insert(0,'/Users/dskilton/conductor/workspaces/sixies_development/port-louis/tests/amiga/uae4arm')
__file__='/Users/dskilton/conductor/workspaces/sixies_development/port-louis/tests/amiga/uae4arm/check_machine.py'
#!/usr/bin/env python3
"""Bounded ARM instruction-model chipset check; optional boot requires private media.
No cache/MMU or physical timing claim. Boot can take several minutes.
"""
from pathlib import Path
import sys,struct,subprocess,time,json,hashlib
from unicorn import *
from unicorn.arm_const import *
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'amiga/uae4arm'))
from elf import unpack
out=root/'.context/amiga/uae4arm';base=0x12000040;block=0x4000000 if '--cache32' in sys.argv else 0x2000000
elf=Path(sys.argv[sys.argv.index('--elf')+1]) if '--elf' in sys.argv else out/'uae-machine.elf'
image,rel,_=unpack(elf.read_bytes(),allocation_size=block)
for at in rel:struct.pack_into('<I',image,at,struct.unpack_from('<I',image,at)[0]+base)
symbol_rows=[p for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',elf],text=True).splitlines() if len(p:=line.split())==3]
sym={p[2]:int(p[0],16)+base for p in symbol_rows}
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
buffer_calls = {}
if '--buffer-report' in sys.argv:
 # Count actual out-of-line calls, not elapsed time or all memory traffic.
 # Compiler-inlined copies/clears are deliberately outside this measurement.
 def buffer_entry(uc, address, size, data):
  name = 'memcpy' if address == sym['memcpy'] else 'memset'
  frame = struct.unpack('<I', uc.mem_read(sym['timeframes'], 4))[0]
  phase = 'before-first-frame' if frame == 0 else 'after-first-frame'
  caller = uc.reg_read(UC_ARM_REG_LR) - base - 4
  key = (phase, name, caller)
  row = buffer_calls.setdefault(key, {'calls': 0, 'bytes': 0, 'max_bytes': 0})
  length = uc.reg_read(UC_ARM_REG_R2)
  row['calls'] += 1; row['bytes'] += length
  row['max_bytes'] = max(row['max_bytes'], length)
 for name in ('memcpy', 'memset'):
  u.hook_add(UC_HOOK_CODE, buffer_entry, begin=sym[name], end=sym[name])
if '--trace-halt' in sys.argv:
 def halted(uc,*args):
  pc,pointer,origin=struct.unpack('<3I',uc.mem_read(sym['regs']+72,12))
  opcode=struct.unpack('<H',uc.mem_read(sym['regs']+84,2))[0]
  frame=struct.unpack('<I',uc.mem_read(sym['timeframes'],4))[0]
  print('GUEST_REGS', ['%08x'%v for v in struct.unpack('<16I',uc.mem_read(sym['regs'],64))],flush=True)
  raise RuntimeError('guest halt reason=%d pc=%08x opcode=%04x frame=%d' % (uc.reg_read(UC_ARM_REG_R0),(pc+pointer-origin)&0xffffffff,opcode,frame))
 u.hook_add(UC_HOOK_CODE,halted,begin=sym['_Z8cpu_halti'],end=sym['_Z8cpu_halti'])
neon_calls=[];neon_half_calls=[]
if '--neon' in sys.argv:
 u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
 for i in range(32):u.reg_write(UC_ARM_REG_D0+i,0x123456789abcdef0^i)
 u.reg_write(UC_ARM_REG_FPSCR,0x01000000)
 def cpacr(uc,address,*args):
  uc.reg_write(UC_ARM_REG_R1,uc.reg_read(UC_ARM_REG_C1_C0_2));uc.reg_write(UC_ARM_REG_PC,address+4)
 u.hook_add(UC_HOOK_CODE,cpacr,begin=sym['zu_neon_available'],end=sym['zu_neon_available'])
 def neon_call(*args):neon_calls.append(1)
 u.hook_add(UC_HOOK_CODE,neon_call,begin=sym['zu_convert_neon'],end=sym['zu_convert_neon'])
 if '--require-neon-half' in sys.argv:
  u.hook_add(UC_HOOK_CODE,lambda *args:neon_half_calls.append(1),begin=sym['zu_convert_neon320'],end=sym['zu_convert_neon320'])
u.mem_map(base&~4095,block+8192);u.mem_write(base,bytes(image));u.mem_map(0xf8f00000,4096)
u.mem_write(base+0x480000,bytes.fromhex('0000a0e31eff2fe1'))
u.mem_write(sym['uae_shared'],struct.pack('<I',base))
ide_image=None
if '--ide-fixture' in sys.argv:
 ide_image=bytearray((i*7+3)&255 for i in range(8*1024*1024))
 u.mem_write(base+0x483148,struct.pack('>2I',len(ide_image),1))
 def storage_reply(uc,kind,a,n,v,data):
  seq,op,unit,offset,length=struct.unpack('>5I',uc.mem_read(base+0x483100,20))
  assert unit==2 and op in (1,2) and 0<length<=16384 and offset+length<=len(ide_image)
  if op==1:uc.mem_write(base+0x488000,bytes(ide_image[offset:offset+length]))
  else:ide_image[offset:offset+length]=uc.mem_read(base+0x488000,length)
  uc.mem_write(base+0x483140,struct.pack('>2I',seq,length))
 u.hook_add(UC_HOOK_MEM_READ,storage_reply,begin=base+0x483140,end=base+0x483140)
if '--rtc' in sys.argv:
 u.mem_write(base+0x482868,struct.pack('>2I',1,1793188800))
if '--ntsc' in sys.argv:u.mem_write(base+0x482878,struct.pack('>I',1))
df1_data=None
if '--df1' in sys.argv:
 df1_data=bytes(range(256))*(901120//256)
 u.mem_write(sym['zzuae_disk1_image'],df1_data)
 u.mem_write(base+0x482860,struct.pack('>I',1))
if '--disable-jit-nibbles' in sys.argv or '--disable-byte-destination' in sys.argv:
 disabled={int(n,16) for n in sys.argv[sys.argv.index('--disable-jit-nibbles')+1].split(',')} if '--disable-jit-nibbles' in sys.argv else set()
 destination=sys.argv[sys.argv.index('--disable-byte-destination')+1] if '--disable-byte-destination' in sys.argv else None
 def filter_translator(uc,*args):
  if uc.reg_read(UC_ARM_REG_R0)!=1:return
  for table_name in ['_ZL11compfunctbl','_ZL13nfcompfunctbl']:
   for n in disabled:uc.mem_write(sym[table_name]+n*4096*4,bytes(4096*4))
   if destination:
    for op in range(0x1000,0x2000):
     if (((op>>6)&7)==0)==(destination=='register'):uc.mem_write(sym[table_name]+op*4,bytes(4))
 u.hook_add(UC_HOOK_CODE,filter_translator,begin=sym['_Z15set_cache_statei'],end=sym['_Z15set_cache_statei'])
if '--engine' in sys.argv:
 engine=int(sys.argv[sys.argv.index('--engine')+1]);assert engine in (1,2)
 assert 'zzuae_run_accelerated' in sym,'player has no accelerated CPU integration'
 u.mem_write(base+0x48282c,struct.pack('>I',engine))
 table=(base+0x400000+16383)&~16383;l2=table+16384
 for index,section in enumerate(range(base>>20,(base+block-1>>20)+1)):
  leaf=l2+index*1024;u.mem_write(table+section*4,struct.pack('<I',leaf|1))
  for n in range(256):
   page=(section<<20)+(n<<12)
   u.mem_write(leaf+n*4,struct.pack('<I',page|0x117))
if len(sys.argv)>1:
 if '--synthetic-rom' not in sys.argv:
  u.mem_write(base+0x4e0000,(out/'media/kick12.rom').read_bytes())
  u.mem_write(base+0x560000,(out/'media/wb12.adf').read_bytes())
 requested=int(sys.argv[1])
 u.mem_write(base+0x482800,struct.pack('>I',requested))
profile=None
if '--profile' in sys.argv:
 profile=int(sys.argv[sys.argv.index('--profile')+1]);assert 0<=profile<5
 u.mem_write(base+0x482814,struct.pack('>I',profile+1))
 expanded='--ram1m' in sys.argv
 if '--synthetic-rom' in sys.argv:
  rom=bytearray(524288 if profile>=2 else 262144)
  pc=0xf80040 if profile>=2 else 0xfc0040
  struct.pack_into('>II',rom,0,0x20000,pc)
  struct.pack_into('>HH',rom,12,37 if profile>=2 else 33 if profile==0 else 34,350 if profile in (3,4) else 175)
  rom[64:]=bytes.fromhex('33fc0f0000dff18060fe')+rom[74:]
  u.mem_write(base+0x4e0000,bytes(rom))
 else:
  path=out/'media'/('kick12.rom' if profile==0 else 'kick13-clean.rom' if profile==1 else 'kick204.rom' if profile==2 else 'kick205.rom')
  u.mem_write(base+0x4e0000,path.read_bytes())
if '--rom' in sys.argv:u.mem_write(base+0x4e0000,Path(sys.argv[sys.argv.index('--rom')+1]).read_bytes())
if '--fpu-fixture' in sys.argv:
 u.mem_write(base+0x482848,struct.pack('>I',0 if '--fpu-off' in sys.argv else 1))
 program=(out/'fpu-execution/fpu_guest.bin').read_bytes()
 u.mem_write(base+0x4e0040,program)
live='--live' in sys.argv or '--direct-live' in sys.argv
direct_live='--direct-live' in sys.argv
live_seen=[]
if live:
 u.mem_write(base+0x482804,struct.pack('>I',24 if direct_live else 8))
 wait_reads={};held={}
 if direct_live:
  direct_height=512 if "--hires" in sys.argv else 480
  direct_address=0x003ff000;direct_span=640*direct_height*4
  u.mem_map(0x00300000,0x300000)
  grants=[]
  def grant(u,kind,address,size,value,data):
   p=base+0x482c00;seq=struct.unpack('>I',u.mem_read(p,4))[0]
   if not seq or seq in grants:return
   assert not grants or grants[-1] in live_seen,'new grant before previous frame acknowledged'
   nonce=seq^0xabcd1234
   u.mem_write(direct_address,struct.pack('>I',nonce))
   u.mem_write(direct_address+direct_span-4,struct.pack('>I',nonce^0x31415926))
   u.mem_write(p+76,struct.pack('>4I',direct_address,2560,3,nonce))
   u.mem_write(p+100,struct.pack('>2I',640,direct_height))
   u.mem_write(p+72,struct.pack('>I',seq));grants.append(seq)
  u.hook_add(UC_HOOK_MEM_READ,grant,begin=base+0x482c48,end=base+0x482c4b)
 def acknowledge(u,kind,address,size,value,data):
  p=base+0x482c00
  seq=struct.unpack('>I',u.mem_read(p,4))[0]
  ack=struct.unpack('>I',u.mem_read(p+64,4))[0]
  if not seq or seq==ack:return
  image_at=direct_address if direct_live else base+0x490000
  image_size=direct_span if direct_live else 327680
  if direct_live:
   assert struct.unpack('>2I',u.mem_read(p+8,8))==(seq,0),'ACK before ARM render completion'
  wait_reads[seq]=wait_reads.get(seq,0)+1
  if wait_reads[seq]==1:held[seq]=bytes(u.mem_read(image_at,image_size))
  if wait_reads[seq]==16:
   assert bytes(u.mem_read(image_at,image_size))==held[seq], 'published frame changed before acknowledgement'
   if seq==1:
    u.mem_write(p+256,struct.pack('>2I',0x10040,0x100c0))
    u.mem_write(p+68,struct.pack('>I',2))
   u.mem_write(p+64,struct.pack('>I',seq));live_seen.append(seq)
 u.hook_add(UC_HOOK_MEM_READ,acknowledge,begin=base+0x482c40,end=base+0x482c43)
if '--ram1m' in sys.argv:
 flags=struct.unpack('>I',u.mem_read(base+0x482804,4))[0]
 u.mem_write(base+0x482804,struct.pack('>I',flags|32))
audio='--audio' in sys.argv
pcm_blocks=[]
if audio:
 flags=struct.unpack('>I',u.mem_read(base+0x482804,4))[0]
 u.mem_write(base+0x482804,struct.pack('>I',flags|64))
 u.mem_write(base+0x483044,struct.pack('>I',32000))
 rate=int(sys.argv[sys.argv.index('--display-rate')+1]) if '--display-rate' in sys.argv else 25
 u.mem_write(base+0x482828,struct.pack('>I',rate))
 if '--audio-pressure' in sys.argv:u.mem_write(base+0x48304c,struct.pack('>I',1))
 if '--synthetic-rom' in sys.argv:
  program=bytearray.fromhex("13fc000200bfe001") # CIA-A: remove ROM overlay before filling Chip RAM
  def movew(v,a):program.extend(struct.pack('>HHI',0x33fc,v,a))
  for i in range(16):movew(0x4040 if i<8 else 0xc0c0,0x2000+i*2)
  for channel in range(2):
   reg=0xdff0a0+channel*16
   for offset,value in [(0,0),(2,0x2000),(4,16),(6,200+channel*200),(8,64)]:movew(value,reg+offset)
  movew(0x8203,0xdff096)
  program.extend(bytes.fromhex('5287538760fa')) # hot fixed-cycle work while Paula DMA runs
  u.mem_write(base+0x4e0040,bytes(program))
 def consume_audio(u,*args):
  if '--audio-pressure' in sys.argv:
   frame=struct.unpack('<I',u.mem_read(sym['timeframes'],4))[0]
   u.mem_write(base+0x483048,struct.pack('>I',0 if frame<requested//2 else 3072))
  w,r=struct.unpack('>I',u.mem_read(base+0x483000,4))[0],struct.unpack('>I',u.mem_read(base+0x483040,4))[0]
  assert (w-r)&0xffffffff<=4
  while r!=w:
   pcm_blocks.append(bytes(u.mem_read(base+0x484000+(r%4)*4096,4096)));r=(r+1)&0xffffffff
  u.mem_write(base+0x483040,struct.pack('>I',r))
 u.hook_add(UC_HOOK_MEM_READ,consume_audio,begin=base+0x483040,end=base+0x483043)
if '--timing-fixture' in sys.argv:
 assert '--synthetic-rom' in sys.argv and profile is not None
 kind=sys.argv[sys.argv.index('--timing-fixture')+1]
 assert kind in ('beam','branch','irq','pressure','groups','bits','memory')
 program=bytearray.fromhex('13fc000200bfe001') # remove ROM overlay
 if kind=='irq':
  vector=len(program)
  program.extend(struct.pack('>HII',0x23fc,0,0x6c))
  program.extend(bytes.fromhex('46fc200033fcc02000dff09a'))
 if kind=='bits':program.extend(bytes.fromhex('7201')) # nonzero register shift count
 if kind=='pressure':
  program.extend(bytes.fromhex('7c7f528751cefffc')) # warm one translated site
 loop=len(program)
 program.extend(bytes.fromhex('303900dff006')) # VHPOSR before work
 if kind in ('pressure','groups'):
  # Memory operations force separate traces even when register grouping is on.
  program.extend(bytes.fromhex('4a10' if kind=='pressure' else '4e71')*(20000 if kind=='pressure' else 1024))
 elif kind=='memory':
  # 68020 aligned/unaligned data reads, a ROM read and normal MMIO timing.
  assert profile==4
  program.extend(bytes.fromhex('23fc1122334400010000203900010000223900010001'
   '34390001000116390001000323c00000210023c10000210423c20000210823c30000210c'
   '283900f8000023c400002110'))
 elif kind=='bits':
  # Register bit operations, condition-byte writes and all shift/rotate classes.
  program.extend(bytes.fromhex('0800001f0840000f0880000708c0000057c3e2a0e3a0e2a8e3a8e2b8e3b8e2b0e3b0e318e258e330e270')*8)
 elif kind=='irq':
  program.extend(bytes.fromhex('4e71')*8)
  program.extend(bytes.fromhex('33fc802000dff09c')) # force level-3 IRQ
 elif kind=='beam':
  program.extend(bytes.fromhex('5281')*24)
 else:
  # Repeated DBRA sees both taken and expired paths at the same PC.
  program.extend(bytes.fromhex('7207528251c9fffc'))
 program.extend(bytes.fromhex('343900dff00633c00000200033c200002002'))
 if kind in ('pressure','groups'):program.extend(struct.pack('>Hi',0x60ff,loop-len(program)-2))
 else:program.extend(struct.pack('>Hh',0x6000,loop-len(program)-2))
 if kind=='irq':
  struct.pack_into('>I',program,vector+2,pc+len(program))
  program.extend(bytes.fromhex('528533fc002000dff09c4e73'))
 u.mem_write(base+0x4e0040,bytes(program))
if '--copper-fixture' in sys.argv:
 from copper_fixture import program as copper_program
 assert '--synthetic-rom' in sys.argv and profile in (1,4)
 fixture=sys.argv[sys.argv.index('--copper-fixture')+1]
 assert fixture in ('horizontal','skip','cpuwrites','colorwrite','listtoggle','restart','lineend')
 u.mem_write(base+0x4e0040,copper_program(fixture,audio))
u.mem_write(base+0x4e0040,b'\x13\xfc\x00\x02\x00\xbf\xe0\x013\xfc\x00\x00\x00\xdf\xf1\x803\xfc\x01%\x00\xdf\xf1\x823\xfc\x02J\x00\xdf\xf1\x843\xfc\x03o\x00\xdf\xf1\x863\xfc\x04\x94\x00\xdf\xf1\x883\xfc\x05\xb9\x00\xdf\xf1\x8a3\xfc\x06\xde\x00\xdf\xf1\x8c3\xfc\x08\x03\x00\xdf\xf1\x8e3\xfc\t(\x00\xdf\xf1\x903\xfc\nM\x00\xdf\xf1\x923\xfc\x0br\x00\xdf\xf1\x943\xfc\x0c\x97\x00\xdf\xf1\x963\xfc\r\xbc\x00\xdf\xf1\x983\xfc\x0e\xe1\x00\xdf\xf1\x9a3\xfc\x00\x06\x00\xdf\xf1\x9c3\xfc\x01+\x00\xdf\xf1\x9e3\xfc\x02P\x00\xdf\xf1\xa03\xfc\x03u\x00\xdf\xf1\xa23\xfc\x04\x9a\x00\xdf\xf1\xa43\xfc\x05\xbf\x00\xdf\xf1\xa63\xfc\x06\xe4\x00\xdf\xf1\xa83\xfc\x08\t\x00\xdf\xf1\xaa3\xfc\t.\x00\xdf\xf1\xac3\xfc\nS\x00\xdf\xf1\xae3\xfc\x0bx\x00\xdf\xf1\xb03\xfc\x0c\x9d\x00\xdf\xf1\xb23\xfc\r\xc2\x00\xdf\xf1\xb43\xfc\x0e\xe7\x00\xdf\xf1\xb63\xfc\x00\x0c\x00\xdf\xf1\xb83\xfc\x011\x00\xdf\xf1\xba3\xfc\x02V\x00\xdf\xf1\xbc3\xfc\x03{\x00\xdf\xf1\xbe3\xfc\xa5Z\x00\x00P\x003\xfc\xa5\x13\x00\x00P\x023\xfc\xa5\xc8\x00\x00P\x043\xfc\xa5\x81\x00\x00P\x063\xfc\xa4~\x00\x00P\x083\xfc\xa47\x00\x00P\n3\xfc\xa4\xec\x00\x00P\x0c3\xfc\xa4\xa5\x00\x00P\x0e3\xfc\xa7\x12\x00\x00P\x103\xfc\xa7\xcb\x00\x00P\x123\xfc\xa7\x80\x00\x00P\x143\xfc\xa6y\x00\x00P\x163\xfc\xa66\x00\x00P\x183\xfc\xa6\xef\x00\x00P\x1a3\xfc\xa6\xa4\x00\x00P\x1c3\xfc\xa1\x1d\x00\x00P\x1e3\xfc\xa1\xca\x00\x00P 3\xfc\xa1\x83\x00\x00P"3\xfc\xa0x\x00\x00P$3\xfc\xa01\x00\x00P&3\xfc\xa0\xee\x00\x00P(3\xfc\xa0\xa7\x00\x00P*3\xfc\xa3\x1c\x00\x00P,3\xfc\xa3\xd5\x00\x00P.3\xfc\xa3\x82\x00\x00P03\xfc\xa2{\x00\x00P23\xfc\xa20\x00\x00P43\xfc\xa2\xe9\x00\x00P63\xfc\xa2\xa6\x00\x00P83\xfc\xad\x1f\x00\x00P:3\xfc\xad\xd4\x00\x00P<3\xfc\xad\x8d\x00\x00P>3\xfc\xacz\x00\x00P@3\xfc\xac3\x00\x00PB3\xfc\xac\xe8\x00\x00PD3\xfc\xac\xa1\x00\x00PF3\xfc\xaf\x1e\x00\x00PH3\xfc\xaf\xd7\x00\x00PJ3\xfc\xaf\x8c\x00\x00PL3\xfc\xaeE\x00\x00PN3\xfc\xae2\x00\x00PP3\xfc\xae\xeb\x00\x00PR3\xfc\xae\xa0\x00\x00PT3\xfc\xa9\x19\x00\x00PV3\xfc\xa9\xd6\x00\x00PX3\xfc\xa9\x8f\x00\x00PZ3\xfc\xa8D\x00\x00P\\3\xfc\xa8=\x00\x00P^3\xfc\xa8\xea\x00\x00P`3\xfc\xa8\xa3\x00\x00Pb3\xfc\xab\x18\x00\x00Pd3\xfc\xab\xd1\x00\x00Pf3\xfc\xab\x8e\x00\x00Ph3\xfc\xaaG\x00\x00Pj3\xfc\xaa<\x00\x00Pl3\xfc\xaa\xf5\x00\x00Pn3\xfc\xaa\xa2\x00\x00Pp3\xfc\xb5\x1b\x00\x00Pr3\xfc\xb5\xd0\x00\x00Pt3\xfc\xb5\x89\x00\x00Pv3\xfc\xb4F\x00\x00Px3\xfc\xb4?\x00\x00Pz3\xfc\xb4\xf4\x00\x00P|3\xfc\xb4\xad\x00\x00P~3\xfc\xb7\x1a\x00\x00P\x803\xfc\xb7\xd3\x00\x00P\x823\xfc\xb7\x88\x00\x00P\x843\xfc\xb6A\x00\x00P\x863\xfc\xb6>\x00\x00P\x883\xfc\xb6\xf7\x00\x00P\x8a3\xfc\xb6\xac\x00\x00P\x8c3\xfc\xb1e\x00\x00P\x8e3\xfc\xb1\xd2\x00\x00P\x903\xfc\xb1\x8b\x00\x00P\x923\xfc\xb0@\x00\x00P\x943\xfc\xb09\x00\x00P\x963\xfc\xb0\xf6\x00\x00P\x983\xfc\xb0\xaf\x00\x00P\x9a3\xfc\xb3d\x00\x00P\x9c3\xfc\xb3\xdd\x00\x00P\x9e3\xfc\xb3\x8a\x00\x00P\xa03\xfc\xb2C\x00\x00P\xa23\xfc\xb28\x00\x00P\xa43\xfc\xb2\xf1\x00\x00P\xa63\xfc\xb2\xae\x00\x00P\xa83\xfc\xbdg\x00\x00P\xaa3\xfc\xbd\xdc\x00\x00P\xac3\xfc\xbd\x95\x00\x00P\xae3\xfc\xbcB\x00\x00P\xb03\xfc\xbc;\x00\x00P\xb23\xfc\xbc\xf0\x00\x00P\xb43\xfc\xbc\xa9\x00\x00P\xb63\xfc\xbff\x00\x00P\xb83\xfc\xbf\xdf\x00\x00P\xba3\xfc\xbf\x94\x00\x00P\xbc3\xfc\xbeM\x00\x00P\xbe3\xfc\xbe:\x00\x00P\xc03\xfc\xbe\xf3\x00\x00P\xc23\xfc\xbe\xa8\x00\x00P\xc43\xfc\xb9a\x00\x00P\xc63\xfc\xb9\xde\x00\x00P\xc83\xfc\xb9\x97\x00\x00P\xca3\xfc\xb8L\x00\x00P\xcc3\xfc\xb8\x05\x00\x00P\xce3\xfc\xb8\xf2\x00\x00P\xd03\xfc\xb8\xab\x00\x00P\xd23\xfc\xbb`\x00\x00P\xd43\xfc\xbb\xd9\x00\x00P\xd63\xfc\xbb\x96\x00\x00P\xd83\xfc\xbaO\x00\x00P\xda3\xfc\xba\x04\x00\x00P\xdc3\xfc\xba\xfd\x00\x00P\xde3\xfc\xba\xaa\x00\x00P\xe03\xfc\x85c\x00\x00P\xe23\xfc\x85\xd8\x00\x00P\xe43\xfc\x85\x91\x00\x00P\xe63\xfc\x84N\x00\x00P\xe83\xfc\x84\x07\x00\x00P\xea3\xfc\x84\xfc\x00\x00P\xec3\xfc\x84\xb5\x00\x00P\xee3\xfc\x87b\x00\x00P\xf03\xfc\x87\xdb\x00\x00P\xf23\xfc\x87\x90\x00\x00P\xf43\xfc\x86I\x00\x00P\xf63\xfc\x86\x06\x00\x00P\xf83\xfc\x86\xff\x00\x00P\xfa3\xfc\x86\xb4\x00\x00P\xfc3\xfc\x81m\x00\x00P\xfe3\xfc\x81\xda\x00\x00Q\x003\xfc\x81\x93\x00\x00Q\x023\xfc\x80H\x00\x00Q\x043\xfc\x80\x01\x00\x00Q\x063\xfc\x80\xfe\x00\x00Q\x083\xfc\x80\xb7\x00\x00Q\n3\xfc\x83l\x00\x00Q\x0c3\xfc\x83%\x00\x00Q\x0e3\xfc\x83\x92\x00\x00Q\x103\xfc\x82K\x00\x00Q\x123\xfc\x82\x00\x00\x00Q\x143\xfc\x82\xf9\x00\x00Q\x163\xfc\x82\xb6\x00\x00Q\x183\xfc\x8do\x00\x00Q\x1a3\xfc\x8d$\x00\x00Q\x1c3\xfc\x8d\x9d\x00\x00Q\x1e3\xfc\x8cJ\x00\x00Q 3\xfc\x8c\x03\x00\x00Q"3\xfc\x8c\xf8\x00\x00Q$3\xfc\x8c\xb1\x00\x00Q&3\xfc\x8fn\x00\x00Q(3\xfc\x8f\'\x00\x00Q*3\xfc\x8f\x9c\x00\x00Q,3\xfc\x8eU\x00\x00Q.3\xfc\x8e\x02\x00\x00Q03\xfc\x8e\xfb\x00\x00Q23\xfc\x8e\xb0\x00\x00Q43\xfc\x89i\x00\x00Q63\xfc\x89&\x00\x00Q83\xfc\x89\x9f\x00\x00Q:3\xfc\x88T\x00\x00Q<3\xfc\x88\r\x00\x00Q>3\xfc\x88\xfa\x00\x00Q@3\xfc\x88\xb3\x00\x00QB3\xfc\x8bh\x00\x00QD3\xfc\x8b!\x00\x00QF3\xfc\x8b\x9e\x00\x00QH3\xfc\x8aW\x00\x00QJ3\xfc\x8a\x0c\x00\x00QL3\xfc\x8a\xc5\x00\x00QN3\xfc\x8a\xb2\x00\x00QP3\xfc\x95k\x00\x00QR3\xfc\x95 \x00\x00QT3\xfc\x95\x99\x00\x00QV3\xfc\x94V\x00\x00QX3\xfc\x94\x0f\x00\x00QZ3\xfc\x94\xc4\x00\x00Q\\3\xfc\x94\xbd\x00\x00Q^3\xfc\x97j\x00\x00Q`3\xfc\x97#\x00\x00Qb3\xfc\x97\x98\x00\x00Qd3\xfc\x96Q\x00\x00Qf3\xfc\x96\x0e\x00\x00Qh3\xfc\x96\xc7\x00\x00Qj3\xfc\x96\xbc\x00\x00Ql3\xfc\x91u\x00\x00Qn3\xfc\x91"\x00\x00Qp3\xfc\x91\x9b\x00\x00Qr3\xfc\x90P\x00\x00Qt3\xfc\x90\t\x00\x00Qv3\xfc\x90\xc6\x00\x00Qx3\xfc\x90\xbf\x00\x00Qz3\xfc\x93t\x00\x00Q|3\xfc\x93-\x00\x00Q~3\xfc\x93\x9a\x00\x00Q\x803\xfc\x92S\x00\x00Q\x823\xfc\x92\x08\x00\x00Q\x843\xfc\x92\xc1\x00\x00Q\x863\xfc\x92\xbe\x00\x00Q\x883\xfc\x9dw\x00\x00Q\x8a3\xfc\x9d,\x00\x00Q\x8c3\xfc\x9d\xe5\x00\x00Q\x8e3\xfc\x9cR\x00\x00Q\x903\xfc\x9c\x0b\x00\x00Q\x923\xfc\x9c\xc0\x00\x00Q\x943\xfc\x9c\xb9\x00\x00Q\x963\xfc\x9fv\x00\x00Q\x983\xfc\x9f/\x00\x00Q\x9a3\xfc\x9f\xe4\x00\x00Q\x9c3\xfc\x9e]\x00\x00Q\x9e3\xfc\x9e\n\x00\x00Q\xa03\xfc\x9e\xc3\x00\x00Q\xa23\xfc\x9e\xb8\x00\x00Q\xa43\xfc\x99q\x00\x00Q\xa63\xfc\x99.\x00\x00Q\xa83\xfc\x99\xe7\x00\x00Q\xaa3\xfc\x98\\\x00\x00Q\xac3\xfc\x98\x15\x00\x00Q\xae3\xfc\x98\xc2\x00\x00Q\xb03\xfc\x98\xbb\x00\x00Q\xb23\xfc\x9bp\x00\x00Q\xb43\xfc\x9b)\x00\x00Q\xb63\xfc\x9b\xe6\x00\x00Q\xb83\xfc\x9a_\x00\x00Q\xba3\xfc\x9a\x14\x00\x00Q\xbc3\xfc\x9a\xcd\x00\x00Q\xbe3\xfc\x9a\xba\x00\x00Q\xc03\xfc\xe5s\x00\x00Q\xc23\xfc\xe5(\x00\x00Q\xc43\xfc\xe5\xe1\x00\x00Q\xc63\xfc\xe4^\x00\x00Q\xc83\xfc\xe4\x17\x00\x00Q\xca3\xfc\xe4\xcc\x00\x00Q\xcc3\xfc\xe4\x85\x00\x00Q\xce3\xfc\xe7r\x00\x00Q\xd03\xfc\xe7+\x00\x00Q\xd23\xfc\xe7\xe0\x00\x00Q\xd43\xfc\xe6Y\x00\x00Q\xd63\xfc\xe6\x16\x00\x00Q\xd83\xfc\xe6\xcf\x00\x00Q\xda3\xfc\xe6\x84\x00\x00Q\xdc3\xfc\xe1}\x00\x00Q\xde3\xfc\xe1*\x00\x00Q\xe03\xfc\xe1\xe3\x00\x00Q\xe23\xfc\xe0X\x00\x00Q\xe43\xfc\xe0\x11\x00\x00Q\xe63\xfc\xe0\xce\x00\x00Q\xe83\xfc\xe0\x87\x00\x00Q\xea3\xfc\xe3|\x00\x00Q\xec3\xfc\xe35\x00\x00Q\xee3\xfc\xe3\xe2\x00\x00Q\xf03\xfc\xe2[\x00\x00Q\xf23\xfc\xe2\x10\x00\x00Q\xf43\xfc\xe2\xc9\x00\x00Q\xf63\xfc\xe2\x86\x00\x00Q\xf83\xfc\xed\x7f\x00\x00Q\xfa3\xfc\xed4\x00\x00Q\xfc3\xfc\xed\xed\x00\x00Q\xfe3\xfc\x00\x00\x00\xdf\xf0\xe03\xfcP\x00\x00\xdf\xf0\xe23\xfc\x00\x00\x00\xdf\xf0\xe43\xfcP\x00\x00\xdf\xf0\xe63\xfc\x00\x00\x00\xdf\xf0\xe83\xfcP\x00\x00\xdf\xf0\xea3\xfc\x00\x00\x00\xdf\xf0\xec3\xfcP\x00\x00\xdf\xf0\xee3\xfc01\x00\x000\x003\xfc\xff\xfe\x00\x000\x023\xfc\x01\xfc\x00\x000\x043\xfc\x00\x00\x00\x000\x063\xfc\x01\x00\x00\x000\x083\xfc@\x00\x00\x000\n3\xfc\x01\x02\x00\x000\x0c3\xfc\x03\x90\x00\x000\x0e3\xfc\x01\x80\x00\x000\x103\xfc\x06\xc0\x00\x000\x123\xfc0q\x00\x000\x143\xfc\xff\xfe\x00\x000\x163\xfc\x01\xfc\x00\x000\x183\xfc\x00\x01\x00\x000\x1a3\xfc\x01\x00\x00\x000\x1c3\xfc\xc0\x00\x00\x000\x1e3\xfc\x01\x02\x00\x000 3\xfc\x04\xc5\x00\x000"3\xfc\x01\x80\x00\x000$3\xfc\x0c\x80\x00\x000&3\xfc0\xb1\x00\x000(3\xfc\xff\xfe\x00\x000*3\xfc\x01\xfc\x00\x000,3\xfc\x00\x03\x00\x000.3\xfc\x01\x00\x00\x00003\xfc @\x00\x00023\xfc\x01\x02\x00\x00043\xfc\x05\xfa\x00\x00063\xfc\x01\x80\x00\x00083\xfc\x02@\x00\x000:3\xfc@1\x00\x000<3\xfc\xff\xfe\x00\x000>3\xfc\x01\xfc\x00\x000@3\xfc\x00\x00\x00\x000B3\xfc\x01\x00\x00\x000D3\xfc@\x00\x00\x000F3\xfc\x01\x02\x00\x000H3\xfc\x04\xc0\x00\x000J3\xfc\x01\x80\x00\x000L3\xfc\x07\x90\x00\x000N3\xfc\x00\x94\x00\x000P3\xfc\x00\xd0\x00\x000R3\xfc\x00\x96\x00\x000T3\xfc\x81\x00\x00\x000V3\xfc@q\x00\x000X3\xfc\xff\xfe\x00\x000Z3\xfc\x01\xfc\x00\x000\\3\xfc\x00\x01\x00\x000^3\xfc\x01\x00\x00\x000`3\xfc\xc0\x00\x00\x000b3\xfc\x01\x02\x00\x000d3\xfc\x05\xf5\x00\x000f3\xfc\x01\x80\x00\x000h3\xfc\rP\x00\x000j3\xfc\x00\x94\x00\x000l3\xfc\x00H\x00\x000n3\xfc\x00\x96\x00\x000p3\xfc\x01\x00\x00\x000r3\xfc@\xb1\x00\x000t3\xfc\xff\xfe\x00\x000v3\xfc\x01\xfc\x00\x000x3\xfc\x00\x03\x00\x000z3\xfc\x01\x00\x00\x000|3\xfc @\x00\x000~3\xfc\x01\x02\x00\x000\x803\xfc\x07*\x00\x000\x823\xfc\x01\x80\x00\x000\x843\xfc\x03\x10\x00\x000\x863\xfc\x00\x94\x00\x000\x883\xfc\x00\xd0\x00\x000\x8a3\xfc\x00\x96\x00\x000\x8c3\xfc\x81\x00\x00\x000\x8e3\xfcP1\x00\x000\x903\xfc\xff\xfe\x00\x000\x923\xfc\x01\xfc\x00\x000\x943\xfc\x00\x00\x00\x000\x963\xfc\x01\x00\x00\x000\x983\xfc@\x00\x00\x000\x9a3\xfc\x01\x02\x00\x000\x9c3\xfc\x05\xf0\x00\x000\x9e3\xfc\x01\x80\x00\x000\xa03\xfc\x08`\x00\x000\xa23\xfcPq\x00\x000\xa43\xfc\xff\xfe\x00\x000\xa63\xfc\x01\xfc\x00\x000\xa83\xfc\x00\x01\x00\x000\xaa3\xfc\x01\x00\x00\x000\xac3\xfc\xc0\x00\x00\x000\xae3\xfc\x01\x02\x00\x000\xb03\xfc\x07%\x00\x000\xb23\xfc\x01\x80\x00\x000\xb43\xfc\x0e \x00\x000\xb63\xfcP\xb1\x00\x000\xb83\xfc\xff\xfe\x00\x000\xba3\xfc\x01\xfc\x00\x000\xbc3\xfc\x00\x03\x00\x000\xbe3\xfc\x01\x00\x00\x000\xc03\xfc @\x00\x000\xc23\xfc\x01\x02\x00\x000\xc43\xfc\x08Z\x00\x000\xc63\xfc\x01\x80\x00\x000\xc83\xfc\x03\xe0\x00\x000\xca3\xfc`1\x00\x000\xcc3\xfc\xff\xfe\x00\x000\xce3\xfc\x01\xfc\x00\x000\xd03\xfc\x00\x00\x00\x000\xd23\xfc\x01\x00\x00\x000\xd43\xfc@\x00\x00\x000\xd63\xfc\x01\x02\x00\x000\xd83\xfc\x07 \x00\x000\xda3\xfc\x01\x80\x00\x000\xdc3\xfc\t0\x00\x000\xde3\xfc\x00\x94\x00\x000\xe03\xfc\x00\xd0\x00\x000\xe23\xfc\x00\x96\x00\x000\xe43\xfc\x81\x00\x00\x000\xe63\xfc`q\x00\x000\xe83\xfc\xff\xfe\x00\x000\xea3\xfc\x01\xfc\x00\x000\xec3\xfc\x00\x01\x00\x000\xee3\xfc\x01\x00\x00\x000\xf03\xfc\xc0\x00\x00\x000\xf23\xfc\x01\x02\x00\x000\xf43\xfc\x08U\x00\x000\xf63\xfc\x01\x80\x00\x000\xf83\xfc\x0e\xf0\x00\x000\xfa3\xfc\x00\x94\x00\x000\xfc3\xfc\x00H\x00\x000\xfe3\xfc\x00\x96\x00\x001\x003\xfc\x01\x00\x00\x001\x023\xfc`\xb1\x00\x001\x043\xfc\xff\xfe\x00\x001\x063\xfc\x01\xfc\x00\x001\x083\xfc\x00\x03\x00\x001\n3\xfc\x01\x00\x00\x001\x0c3\xfc @\x00\x001\x0e3\xfc\x01\x02\x00\x001\x103\xfc\t\x8a\x00\x001\x123\xfc\x01\x80\x00\x001\x143\xfc\x04\xb0\x00\x001\x163\xfc\x00\x94\x00\x001\x183\xfc\x00\xd0\x00\x001\x1a3\xfc\x00\x96\x00\x001\x1c3\xfc\x81\x00\x00\x001\x1e3\xfcp1\x00\x001 3\xfc\xff\xfe\x00\x001"3\xfc\x01\xfc\x00\x001$3\xfc\x00\x00\x00\x001&3\xfc\x01\x00\x00\x001(3\xfc@\x00\x00\x001*3\xfc\x01\x02\x00\x001,3\xfc\x08P\x00\x001.3\xfc\x01\x80\x00\x00103\xfc\n\x00\x00\x00123\xfcpq\x00\x00143\xfc\xff\xfe\x00\x00163\xfc\x01\xfc\x00\x00183\xfc\x00\x01\x00\x001:3\xfc\x01\x00\x00\x001<3\xfc\xc0\x00\x00\x001>3\xfc\x01\x02\x00\x001@3\xfc\t\x85\x00\x001B3\xfc\x01\x80\x00\x001D3\xfc\x0f\xc0\x00\x001F3\xfcp\xb1\x00\x001H3\xfc\xff\xfe\x00\x001J3\xfc\x01\xfc\x00\x001L3\xfc\x00\x03\x00\x001N3\xfc\x01\x00\x00\x001P3\xfc @\x00\x001R3\xfc\x01\x02\x00\x001T3\xfc\n\xba\x00\x001V3\xfc\x01\x80\x00\x001X3\xfc\x05\x80\x00\x001Z3\xfc\x801\x00\x001\\3\xfc\xff\xfe\x00\x001^3\xfc\x01\xfc\x00\x001`3\xfc\x00\x00\x00\x001b3\xfc\x01\x00\x00\x001d3\xfc@\x00\x00\x001f3\xfc\x01\x02\x00\x001h3\xfc\t\x80\x00\x001j3\xfc\x01\x80\x00\x001l3\xfc\n\xd0\x00\x001n3\xfc\x00\x94\x00\x001p3\xfc\x00\xd0\x00\x001r3\xfc\x00\x96\x00\x001t3\xfc\x81\x00\x00\x001v3\xfc\x80q\x00\x001x3\xfc\xff\xfe\x00\x001z3\xfc\x01\xfc\x00\x001|3\xfc\x00\x01\x00\x001~3\xfc\x01\x00\x00\x001\x803\xfc\xc0\x00\x00\x001\x823\xfc\x01\x02\x00\x001\x843\xfc\n\xb5\x00\x001\x863\xfc\x01\x80\x00\x001\x883\xfc\x00\x90\x00\x001\x8a3\xfc\x00\x94\x00\x001\x8c3\xfc\x00H\x00\x001\x8e3\xfc\x00\x96\x00\x001\x903\xfc\x01\x00\x00\x001\x923\xfc\x80\xb1\x00\x001\x943\xfc\xff\xfe\x00\x001\x963\xfc\x01\xfc\x00\x001\x983\xfc\x00\x03\x00\x001\x9a3\xfc\x01\x00\x00\x001\x9c3\xfc @\x00\x001\x9e3\xfc\x01\x02\x00\x001\xa03\xfc\x0b\xea\x00\x001\xa23\xfc\x01\x80\x00\x001\xa43\xfc\x06P\x00\x001\xa63\xfc\x00\x94\x00\x001\xa83\xfc\x00\xd0\x00\x001\xaa3\xfc\x00\x96\x00\x001\xac3\xfc\x81\x00\x00\x001\xae3\xfc\x901\x00\x001\xb03\xfc\xff\xfe\x00\x001\xb23\xfc\x01\xfc\x00\x001\xb43\xfc\x00\x00\x00\x001\xb63\xfc\x01\x00\x00\x001\xb83\xfc@\x00\x00\x001\xba3\xfc\x01\x02\x00\x001\xbc3\xfc\n\xb0\x00\x001\xbe3\xfc\x01\x80\x00\x001\xc03\xfc\x0b\xa0\x00\x001\xc23\xfc\x90q\x00\x001\xc43\xfc\xff\xfe\x00\x001\xc63\xfc\x01\xfc\x00\x001\xc83\xfc\x00\x01\x00\x001\xca3\xfc\x01\x00\x00\x001\xcc3\xfc\xc0\x00\x00\x001\xce3\xfc\x01\x02\x00\x001\xd03\xfc\x0b\xe5\x00\x001\xd23\xfc\x01\x80\x00\x001\xd43\xfc\x01`\x00\x001\xd63\xfc\x90\xb1\x00\x001\xd83\xfc\xff\xfe\x00\x001\xda3\xfc\x01\xfc\x00\x001\xdc3\xfc\x00\x03\x00\x001\xde3\xfc\x01\x00\x00\x001\xe03\xfc @\x00\x001\xe23\xfc\x01\x02\x00\x001\xe43\xfc\r\x1a\x00\x001\xe63\xfc\x01\x80\x00\x001\xe83\xfc\x07 \x00\x001\xea3\xfc\xa01\x00\x001\xec3\xfc\xff\xfe\x00\x001\xee3\xfc\x01\xfc\x00\x001\xf03\xfc\x00\x00\x00\x001\xf23\xfc\x01\x00\x00\x001\xf43\xfc@\x00\x00\x001\xf63\xfc\x01\x02\x00\x001\xf83\xfc\x0b\xe0\x00\x001\xfa3\xfc\x01\x80\x00\x001\xfc3\xfc\x0cp\x00\x001\xfe3\xfc\x00\x94\x00\x002\x003\xfc\x00\xd0\x00\x002\x023\xfc\x00\x96\x00\x002\x043\xfc\x81\x00\x00\x002\x063\xfc\xa0q\x00\x002\x083\xfc\xff\xfe\x00\x002\n3\xfc\x01\xfc\x00\x002\x0c3\xfc\x00\x01\x00\x002\x0e3\xfc\x01\x00\x00\x002\x103\xfc\xc0\x00\x00\x002\x123\xfc\x01\x02\x00\x002\x143\xfc\r\x15\x00\x002\x163\xfc\x01\x80\x00\x002\x183\xfc\x020\x00\x002\x1a3\xfc\x00\x94\x00\x002\x1c3\xfc\x00H\x00\x002\x1e3\xfc\x00\x96\x00\x002 3\xfc\x01\x00\x00\x002"3\xfc\xa0\xb1\x00\x002$3\xfc\xff\xfe\x00\x002&3\xfc\x01\xfc\x00\x002(3\xfc\x00\x03\x00\x002*3\xfc\x01\x00\x00\x002,3\xfc @\x00\x002.3\xfc\x01\x02\x00\x00203\xfc\x0eJ\x00\x00223\xfc\x01\x80\x00\x00243\xfc\x07\xf0\x00\x00263\xfc\x00\x94\x00\x00283\xfc\x00\xd0\x00\x002:3\xfc\x00\x96\x00\x002<3\xfc\x81\x00\x00\x002>3\xfc\xb01\x00\x002@3\xfc\xff\xfe\x00\x002B3\xfc\x01\xfc\x00\x002D3\xfc\x00\x00\x00\x002F3\xfc\x01\x00\x00\x002H3\xfc@\x00\x00\x002J3\xfc\x01\x02\x00\x002L3\xfc\r\x10\x00\x002N3\xfc\x01\x80\x00\x002P3\xfc\r@\x00\x002R3\xfc\xb0q\x00\x002T3\xfc\xff\xfe\x00\x002V3\xfc\x01\xfc\x00\x002X3\xfc\x00\x01\x00\x002Z3\xfc\x01\x00\x00\x002\\3\xfc\xc0\x00\x00\x002^3\xfc\x01\x02\x00\x002`3\xfc\x0eE\x00\x002b3\xfc\x01\x80\x00\x002d3\xfc\x03\x00\x00\x002f3\xfc\xb0\xb1\x00\x002h3\xfc\xff\xfe\x00\x002j3\xfc\x01\xfc\x00\x002l3\xfc\x00\x03\x00\x002n3\xfc\x01\x00\x00\x002p3\xfc @\x00\x002r3\xfc\x01\x02\x00\x002t3\xfc\x0fz\x00\x002v3\xfc\x01\x80\x00\x002x3\xfc\x08\xc0\x00\x002z3\xfc\xc01\x00\x002|3\xfc\xff\xfe\x00\x002~3\xfc\x01\xfc\x00\x002\x803\xfc\x00\x00\x00\x002\x823\xfc\x01\x00\x00\x002\x843\xfc@\x00\x00\x002\x863\xfc\x01\x02\x00\x002\x883\xfc\x0e@\x00\x002\x8a3\xfc\x01\x80\x00\x002\x8c3\xfc\x0e\x10\x00\x002\x8e3\xfc\x00\x94\x00\x002\x903\xfc\x00\xd0\x00\x002\x923\xfc\x00\x96\x00\x002\x943\xfc\x81\x00\x00\x002\x963\xfc\xc0q\x00\x002\x983\xfc\xff\xfe\x00\x002\x9a3\xfc\x01\xfc\x00\x002\x9c3\xfc\x00\x01\x00\x002\x9e3\xfc\x01\x00\x00\x002\xa03\xfc\xc0\x00\x00\x002\xa23\xfc\x01\x02\x00\x002\xa43\xfc\x0fu\x00\x002\xa63\xfc\x01\x80\x00\x002\xa83\xfc\x03\xd0\x00\x002\xaa3\xfc\x00\x94\x00\x002\xac3\xfc\x00H\x00\x002\xae3\xfc\x00\x96\x00\x002\xb03\xfc\x01\x00\x00\x002\xb23\xfc\xc0\xb1\x00\x002\xb43\xfc\xff\xfe\x00\x002\xb63\xfc\x01\xfc\x00\x002\xb83\xfc\x00\x03\x00\x002\xba3\xfc\x01\x00\x00\x002\xbc3\xfc @\x00\x002\xbe3\xfc\x01\x02\x00\x002\xc03\xfc\x10\xaa\x00\x002\xc23\xfc\x01\x80\x00\x002\xc43\xfc\t\x90\x00\x002\xc63\xfc\x00\x94\x00\x002\xc83\xfc\x00\xd0\x00\x002\xca3\xfc\x00\x96\x00\x002\xcc3\xfc\x81\x00\x00\x002\xce3\xfc\xd01\x00\x002\xd03\xfc\xff\xfe\x00\x002\xd23\xfc\x01\xfc\x00\x002\xd43\xfc\x00\x00\x00\x002\xd63\xfc\x01\x00\x00\x002\xd83\xfc@\x00\x00\x002\xda3\xfc\x01\x02\x00\x002\xdc3\xfc\x0fp\x00\x002\xde3\xfc\x01\x80\x00\x002\xe03\xfc\x0e\xe0\x00\x002\xe23\xfc\xd0q\x00\x002\xe43\xfc\xff\xfe\x00\x002\xe63\xfc\x01\xfc\x00\x002\xe83\xfc\x00\x01\x00\x002\xea3\xfc\x01\x00\x00\x002\xec3\xfc\xc0\x00\x00\x002\xee3\xfc\x01\x02\x00\x002\xf03\xfc\x10\xa5\x00\x002\xf23\xfc\x01\x80\x00\x002\xf43\xfc\x04\xa0\x00\x002\xf63\xfc\xd0\xb1\x00\x002\xf83\xfc\xff\xfe\x00\x002\xfa3\xfc\x01\xfc\x00\x002\xfc3\xfc\x00\x03\x00\x002\xfe3\xfc\x01\x00\x00\x003\x003\xfc @\x00\x003\x023\xfc\x01\x02\x00\x003\x043\xfc\x11\xda\x00\x003\x063\xfc\x01\x80\x00\x003\x083\xfc\n`\x00\x003\n3\xfc\xe01\x00\x003\x0c3\xfc\xff\xfe\x00\x003\x0e3\xfc\x01\xfc\x00\x003\x103\xfc\x00\x00\x00\x003\x123\xfc\x01\x00\x00\x003\x143\xfc@\x00\x00\x003\x163\xfc\x01\x02\x00\x003\x183\xfc\x10\xa0\x00\x003\x1a3\xfc\x01\x80\x00\x003\x1c3\xfc\x0f\xb0\x00\x003\x1e3\xfc\x00\x94\x00\x003 3\xfc\x00\xd0\x00\x003"3\xfc\x00\x96\x00\x003$3\xfc\x81\x00\x00\x003&3\xfc\xe0q\x00\x003(3\xfc\xff\xfe\x00\x003*3\xfc\x01\xfc\x00\x003,3\xfc\x00\x01\x00\x003.3\xfc\x01\x00\x00\x00303\xfc\xc0\x00\x00\x00323\xfc\x01\x02\x00\x00343\xfc\x11\xd5\x00\x00363\xfc\x01\x80\x00\x00383\xfc\x05p\x00\x003:3\xfc\x00\x94\x00\x003<3\xfc\x00H\x00\x003>3\xfc\x00\x96\x00\x003@3\xfc\x01\x00\x00\x003B3\xfc\xe0\xb1\x00\x003D3\xfc\xff\xfe\x00\x003F3\xfc\x01\xfc\x00\x003H3\xfc\x00\x03\x00\x003J3\xfc\x01\x00\x00\x003L3\xfc @\x00\x003N3\xfc\x01\x02\x00\x003P3\xfc\x13\n\x00\x003R3\xfc\x01\x80\x00\x003T3\xfc\x0b0\x00\x003V3\xfc\x00\x94\x00\x003X3\xfc\x00\xd0\x00\x003Z3\xfc\x00\x96\x00\x003\\3\xfc\x81\x00\x00\x003^3\xfc\xff\xff\x00\x003`3\xfc\xff\xfe\x00\x003b3\xfc,\x81\x00\xdf\xf0\x8e3\xfc,\xc1\x00\xdf\xf0\x903\xfc\x008\x00\xdf\xf0\x923\xfc\x00\xd0\x00\xdf\xf0\x943\xfc@\x00\x00\xdf\xf1\x003\xfc\x00\x00\x00\xdf\xf0\x803\xfc0\x00\x00\xdf\xf0\x823\xfc\x83\x80\x00\xdf\xf0\x963\xfc\x00\x00\x00\xdf\xf0\x88`\xfe')
block_calls=[0,0,0]
def block_enter(uc,address,*args):
 for i in range(3):
  if address==sym['_ZL26beginning_of_plane_block_%di'%i]:block_calls[i]+=1
for i in range(3):
 at=sym['_ZL26beginning_of_plane_block_%di'%i]
 u.hook_add(UC_HOOK_CODE,block_enter,begin=at,end=at)
u.reg_write(UC_ARM_REG_SP,base+block-4112);u.reg_write(UC_ARM_REG_LR,base+0x480100)
for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],[0 if len(sys.argv)>1 else 1,base+0x480200,base+0x480000,base+0x480000]):u.reg_write(r,v)
clock=int(sys.argv[sys.argv.index('--timer-us')+1],0)*333 if '--timer-us' in sys.argv else 0
def timer(u,kind,a,n,v,data):
 global clock
 if a==0xf8f00200:
  clock+=33300;u.mem_write(a,struct.pack('<Q',clock))
u.hook_add(UC_HOOK_MEM_READ,timer,begin=0xf8f00200,end=0xf8f00200)
def fatal(u,a,n,data):raise RuntimeError('abort '+hex(a))
u.hook_add(UC_HOOK_CODE,fatal,begin=sym['abort'],end=sym['abort'])
print('START',len(image),'relocations',len(rel),flush=True)
try:
 for batch in range(120):
  u.emu_start(sym['mesen_test'] if batch==0 else (u.reg_read(UC_ARM_REG_PC)|((u.reg_read(UC_ARM_REG_CPSR)>>5)&1)),base+0x480100,count=100000000)
  if u.reg_read(UC_ARM_REG_PC)==base+0x480100:break
  print('PROGRESS',batch,hex(u.reg_read(UC_ARM_REG_PC)),hex(u.reg_read(UC_ARM_REG_LR)),flush=True)
except Exception as e:print('ERROR',repr(e),'PC',hex(u.reg_read(UC_ARM_REG_PC)),'LR',hex(u.reg_read(UC_ARM_REG_LR)));raise
# Include the final published PCM block regardless of which hook drained it.
if audio:consume_audio(u)
if '--require-neon-bitplanes' in sys.argv:
 rows={name:struct.unpack('<I',u.mem_read(sym[name],4))[0]
       for name in ['zu_bitplanes_neon_rows','zu_bitplanes_scalar_rows']}
 assert rows['zu_bitplanes_neon_rows']>0,rows
 assert all(u.reg_read(UC_ARM_REG_D0+i)==(0x123456789abcdef0^i) for i in range(32))
 assert u.reg_read(UC_ARM_REG_FPSCR)==0x01000000
 print('PASS integrated NEON bitplanes: rows and full SIMD restoration',rows)
if '--engine' in sys.argv:
 translated,fallback=struct.unpack('>2I',u.mem_read(base+0x482830,8))
 assert (translated>0) if engine==1 else (translated==0),(engine,translated)
 assert u.cpr_read(15,0,12,0,0,0,False)==0,'VBAR not restored'
 print('ENGINE',engine,'translated sites',translated,'fallback sites',fallback,flush=True)
 if '--timing-fixture' in sys.argv and kind=='pressure' and engine==1:
  reclaimed=struct.unpack('<I',u.mem_read(sym['zz_jit_metadata_flushes'],4))[0]
  assert reclaimed>0,'metadata budget did not trigger reclamation'
  print('PASS bounded JIT metadata reclamation:',reclaimed,flush=True)
if '--require-event-blocks' in sys.argv and engine==1:
 assert 'zz_jit_max_group' in sym,'candidate has no event-aware grouping'
 counts={name:struct.unpack('<I',u.mem_read(sym[name],4))[0]for name in ['zz_jit_grouped_compiles','zz_jit_max_group','zz_jit_event_fallbacks']}
 if kind in ('beam','irq','groups'):assert counts['zz_jit_max_group']>1,counts
 print('EVENT_BLOCKS',counts,flush=True)
if '--require-jit-profile' in sys.argv:
 magic,total,samples,stage_count=struct.unpack('>4I',u.mem_read(base+0x482980,16))
 assert stage_count==7
 assert magic==0x4a505232 and total==struct.unpack('<I',u.mem_read(base+0x480200,4))[0]
 assert 0<samples<total
 stages=[struct.unpack('>QII',u.mem_read(base+0x482990+16*i,16))for i in range(7)]
 assert sum(stage[0] for stage in stages)>0
 assert stages[2][1]+stages[3][1]==samples
 assert stages[0][1]>=2*samples and stages[4][1]==samples
 if engine==2:assert stages[1][1]==stages[2][1]==0 and stages[3][1]==samples
 print('PASS JIT sampled profile: dispatches',total,'samples',samples,'stages',stages,flush=True)
if '--fpu-fixture' in sys.argv:
 chip=struct.unpack('<I',u.mem_read(sym['chipmem_bank']+32,4))[0]
 values=struct.unpack('>10I',u.mem_read(chip+0x10000,40))
 expected=(0,)*10 if '--fpu-off' in sys.argv else (16,4,0x40030000,0x80000000,0,2,3,2,4,0x46505531)
 assert values==expected,(values,expected)
 for i in range(32):assert u.reg_read(UC_ARM_REG_D0+i)==(0x123456789abcdef0^i),i
 assert u.reg_read(UC_ARM_REG_FPSCR)==0x01000000
 print('PASS: FPU Off rejects guest instructions' if '--fpu-off' in sys.argv else 'PASS: guest FPU arithmetic, sqrt, extended storage, directed rounding, ties-even and full VFP restoration',values)
if '--timing-fixture' in sys.argv and kind=='memory':
 chip=struct.unpack('<I',u.mem_read(sym['chipmem_bank']+32,4))[0]
 values=struct.unpack('>5I',u.mem_read(chip+0x2100,20))
 assert values==(0x11223344,0x22334400,0x2233,0x44,0x20000),values
 print('PASS actual 68020 aligned/unaligned Chip RAM and ROM reads',values)
if '--state-report' in sys.argv:
 # Pinned ARM ABI: addrbank.baseaddr follows eight 32-bit function pointers.
 # Compare guest RAM, register/CCR prefix (no native pointers), frame and PCM.
 chip=struct.unpack('<I',u.mem_read(sym['chipmem_bank']+32,4))[0]
 chip_size=struct.unpack('>I',u.mem_read(base+0x482808,4))[0]
 result=list(struct.unpack('<11I',u.mem_read(base+0x480200,44)))
 result[6]=0 # host timing is deliberately excluded
 digest=lambda address,size:hashlib.sha256(bytes(u.mem_read(address,size))).hexdigest()
 # Compare architectural flags: NZCV uses bits 31..28; GET_XFLG uses bit 0.
 # Compiled code may retain unrelated bits in both backing words.
 registers=bytes(u.mem_read(sym['regs'],64))
 nzcv,x=struct.unpack('<2I',u.mem_read(sym['regs']+64,8))
 cpu_state=registers+struct.pack('<2I',nzcv&0xf0000000,x&1)
 if '--trace-ccr' in sys.argv:print('REGISTERS',struct.unpack('<16I',registers),'NZCV/X',hex(nzcv),hex(x),flush=True)
 state={'result':result,'cpu_registers_ccr':hashlib.sha256(cpu_state).hexdigest(),
        'chip_ram':digest(chip,chip_size),'pixels':digest(base+0x490000,640*256*2),
        'pcm':hashlib.sha256(b''.join(pcm_blocks)).hexdigest()}
 if live and not audio and (direct_live or '--copper-fixture' in sys.argv):
  assert len(live_seen)==requested
  state['frame_hashes']=[hashlib.sha256(held[n]).hexdigest() for n in live_seen]
 Path(sys.argv[sys.argv.index('--state-report')+1]).write_text(json.dumps(state,indent=2)+'\n')
if '--buffer-report' in sys.argv:
 import bisect
 # Keep duplicate local names and exclude data/absolute symbols from attribution.
 symbols = sorted((int(p[0],16), p[2]) for p in symbol_rows if p[1] in ('t','T'))
 addresses = [address for address, name in symbols]
 rows = []
 for (phase, function, caller), counts in sorted(buffer_calls.items()):
  index = bisect.bisect_right(addresses, caller) - 1
  origin, name = symbols[index] if index >= 0 else (0, 'unknown')
  rows.append({'phase': phase, 'function': function, 'caller': hex(caller),
               'nearest_symbol': name, 'symbol_offset': caller - origin, **counts})
 report = {'scope': 'out-of-line memcpy/memset calls through main emulation return; excludes inlined operations',
           'rows': rows}
 Path(sys.argv[sys.argv.index('--buffer-report')+1]).write_text(json.dumps(report, indent=2)+'\n')
if '--ram1m' in sys.argv and profile is None:
 assert u.reg_read(UC_ARM_REG_R0)==0
 assert struct.unpack('>3I',u.mem_read(base+0x482808,12))==(524288,524288,1)
 print('PASS: mapped 512K Slow RAM full-bank pattern/alias test and clear')
if profile is not None:
 assert u.reg_read(UC_ARM_REG_R0)==0
 expected_chip=([0x40000,0x80000],[0x80000,0x80000],[0x100000,0x200000],[0x100000,0x200000],[0x200000,0x200000])[profile][int(expanded)]
 expected_slow=0x80000 if profile==1 and expanded else 0
 assert struct.unpack('>3I',u.mem_read(base+0x482808,12))==(expected_chip,expected_slow,1)
 mask,compat,overlay=struct.unpack('>3I',u.mem_read(base+0x482818,12))
 assert mask==(7 if profile==4 else 3 if profile>=2 else 0),(profile,mask)
 assert compat==[8,5,6,7,9][profile] and overlay==(0 if profile in (3,4) else 1)
 print('PASS: profile',profile,'Chip',expected_chip,'Slow',expected_slow,'chipset',mask,'overlay',overlay)
if '--require-early-pressure' in sys.argv:
 drawn,skipped=[struct.unpack('<I',u.mem_read(sym[name],4))[0]for name in ['zu_drawn_frames','zu_skipped_frames']]
 assert drawn+skipped==requested and drawn<requested*rate//50,(drawn,skipped)
 print('PASS pressure skips before drawing:',drawn,skipped,flush=True)
if audio:
 consume_audio(u)
 if '--audio-pressure' in sys.argv:
  deferred=struct.unpack('>I',u.mem_read(base+0x483008,4))[0]
  assert deferred>0 and len(live_seen)>=2,(deferred,live_seen)
  print('PASS audio pressure: deferred display, bounded refresh and continued emulation/input',deferred,len(live_seen))
 raw=b''.join(pcm_blocks)
 print('PCM diagnostics',len(raw),'write',struct.unpack('>I',u.mem_read(base+0x483000,4))[0],'nonzero',struct.unpack('>I',u.mem_read(base+0x483004,4))[0], 'sample_evtime',struct.unpack('<I',u.mem_read(sym['scaled_sample_evtime'],4))[0],flush=True)
 assert raw and any(raw), 'silent or absent Paula PCM'
 samples=list(struct.iter_unpack('>hh',raw))
 assert any(l and r for l,r in samples), 'missing stereo channel'
 assert any(l!=r for l,r in samples), 'stereo collapsed'
 (out/'audio/model-stereo.pcm').write_bytes(raw)
 print('PASS: guest Paula DMA generates stereo BE PCM, frames',len(samples),'nonzero',sum(bool(l or r) for l,r in samples))
print('END',hex(u.reg_read(UC_ARM_REG_PC)),u.reg_read(UC_ARM_REG_R0),struct.unpack('<11I',u.mem_read(base+0x480200,44)),flush=True)
pixels=next((v for k,v in sym.items() if k=='_ZL6pixels'))
(out/('boot.rgb565' if len(sys.argv)>1 else 'machine.rgb565')).write_bytes(u.mem_read(pixels,(640 if len(sys.argv)>1 else 320)*256*2))

assert u.reg_read(UC_ARM_REG_PC)==base+0x480100, 'instruction bound exceeded'

assert u.reg_read(UC_ARM_REG_R0)==0, 'diagnostic failed'
if live:
 assert live_seen and live_seen==list(range(1,len(live_seen)+1)),live_seen
 assert struct.unpack('>I',u.mem_read(base+0x482c04,4))[0]==2,'input was not consumed'
 print('PASS: live publication waits for ACK, holds pixels stable, consumes ordered input',len(live_seen))
if len(sys.argv)>1:
 result=struct.unpack('<11I',u.mem_read(base+0x480200,44))
 assert result[9]==requested,(result,requested)
 print('PASS: big-endian 68K frame request decoded by little-endian ARM:',requested)
 def call(name,*args):
  sp=base+block-4112
  u.mem_write(sp,b'\0'*32)
  u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,base+0x480100)
  for reg,value in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args):u.reg_write(reg,value)
  if len(args)>4:u.mem_write(sp,struct.pack('<%dI'%(len(args)-4),*args[4:]))
  u.emu_start(sym[name],base+0x480100,count=20000000)
  assert u.reg_read(UC_ARM_REG_PC)==base+0x480100,name
  return u.reg_read(UC_ARM_REG_R0)
 if '--cpu-clock-fixture' in sys.argv:
  assert '--synthetic-rom' in sys.argv and '--rom' not in sys.argv and engine==2
  # The pinned 68020 interpreter charges BRA.S nine CPU clocks.
  # A1200 halves that cost in chipset time, preserving the half-clock.
  u.mem_write(sym['uae_frame_limit'],bytes(4))
  counts=base+0x480280
  u.mem_write(counts,bytes(8))
  call('zzuae_run_accelerated',1,counts,counts+4)
  executed,cost=struct.unpack('<2I',u.mem_read(counts,8))
  raw_cost=struct.unpack('<I',u.mem_read(sym['cpu_cycles'],4))[0]
  assert executed==1 and raw_cost==(1152 if profile==4 else 2304),(executed,cost,raw_cost)
  print('PASS CPU/chipset clock ratio: BRA.S cost',cost)
 if ide_image is not None:
  def io(name,*args):return call(next(k for k in sym if name in k),*args)
  def reg(n,v):io('profile_io_bput',0xda2000+n*4,v)
  def sector(lba,count,command):
   reg(6,0xe0|((lba>>24)&15));reg(2,count);reg(3,lba&255);reg(4,(lba>>8)&255);reg(5,(lba>>16)&255);reg(7,command)
  sector(3,2,0x20)
  raw=b''.join(struct.pack('>H',io('profile_io_wget',0xda2000)) for _ in range(512))
  assert raw==ide_image[1536:2560],(raw[:16],ide_image[1536:1552])
  data=bytes((i*13+9)&255 for i in range(1024))
  sector(3,2,0x30)
  for word, in struct.iter_unpack('>H',data):io('profile_io_wput',0xda2000,word)
  assert ide_image[1536:2560]==data
  sector(3,2,0x20)
  raw=b''.join(struct.pack('>H',io('profile_io_wget',0xda2000)) for _ in range(512))
  assert raw==data
  u.mem_write(base+0x48314c,struct.pack('>I',0))
  sector(3,2,0x30)
  for word, in struct.iter_unpack('>H',bytes(1024)):io('profile_io_wput',0xda2000,word)
  assert ide_image[1536:2560]==data, 'read-only HDF changed'
  assert io('profile_io_bget',0xda201c)&1, 'failed write did not report ATA error'
  print('PASS actual ARM Gayle/IDE two-sector read, write and readback')
 # The normal UAE floppy LED callback publishes activity in ARM-owned status.
 for led,state,expected in [(1,1,1),(0,0,1),(1,3,1),(1,0,0)]:
  call('_Z7gui_lediii',led,state,0)
  assert struct.unpack('>I',u.mem_read(base+0x482c20,4))[0]==expected
 print('PASS: DF0 activity on/off and write state; unrelated LEDs leave it unchanged')
 if '--engine' in sys.argv:
  peak,budget=struct.unpack('>2I',u.mem_read(base+0x482870,8))
  assert 0<budget<=2*1024*1024 and budget<=(8*1024*1024-peak)//2
  print('PASS: metadata budget fits startup heap headroom:',peak,budget)
 read_seq=list(struct.unpack('>2I',u.mem_read(base+0x482c24,8)))
 for led,unit,state in [(1,0,1),(1,1,1),(1,2,1),(1,-1,1),(1,0,2),(0,0,1)]:
  call('_Z15gui_flicker_lediii',led,unit&0xffffffff,state)
  if led==1 and unit in (0,1) and state==1:read_seq[unit]=(read_seq[unit]+1)&0xffffffff
  assert list(struct.unpack('>2I',u.mem_read(base+0x482c24,8)))==read_seq
 print('PASS: independent DF0/DF1 read counters; writes and other drives excluded')
 if '--rtc' in sys.argv:
  assert struct.unpack('<I',u.mem_read(sym['mem_banks']+0xdc*4,4))[0]==sym['clock_bank']
  getclock=next(k for k in sym if 'clock_bget' in k)
  def clockreg(n):return call(getclock,0xdc0001+n*4)&15
  expected=[0,0,0,0,2,1,8,2,0,1,6,12,3] if profile<2 else [0,0,0,0,2,1,3,8,2,0,1,6,2]
  assert [clockreg(n) for n in range(13)]==expected
  clock+=666000000
  assert clockreg(0)==2,'RTC must advance with host monotonic time'
  print('PASS: mapped RTC date, weekday, 24-hour time and independent wall-clock advancement')
 if profile==3:
  idput=next(k for k in sym if 'profile_id_bput' in k)
  idget=next(k for k in sym if 'profile_id_bget' in k)
  lowget=next(k for k in sym if 'profile_io_bget' in k)
  call(idput,0xde1000,0)
  assert [call(idget,0xde1000) for _ in range(8)]==[128,128,0,128,0,0,0,0]
  assert call(lowget,0xda201c)==0x7f and call(lowget,0xda9000)==0 and call(lowget,0xda8000)&0x40==0
  print('PASS: empty-slot Gayle identity, IDE status and no card/interrupt')
 buttons='_Z23handle_joystick_buttonshh'
 assert call(buttons,0,0)==0xc0
 for kind,pressed in [(1,0x80),(2,0x40)]:
  call('zzuae_test_button',kind,1);assert call(buttons,0,0)==pressed
  call('zzuae_test_button',kind,0);assert call(buttons,0,0)==0xc0
 u.mem_write(sym['uae_input_mode'],struct.pack('<I',1))
 for frame,wanted in [(899,0xc0),(900,0x80),(910,0xc0)]:
  u.mem_write(sym['timeframes'],struct.pack('<I',frame))
  call('_Z17devices_vsync_prev');assert call(buttons,0,0)==wanted
 u.mem_write(sym['uae_input_mode'],struct.pack('<I',0))
 while call('_Z14keys_availablev'):call('_Z12get_next_keyv')
 call('zzuae_test_button',3,1);call('zzuae_test_button',3,0)
 assert call('_Z12get_next_keyv')==0x80 and call('_Z12get_next_keyv')==0x81
 print('PASS: guest mouse/fire active-low CIA bits; Space press/release keyboard queue')
 # Cross successive guest frames and 8-bit counter wrap, in both directions.
 for dx,dy in [(12,-7),(100,100),(100,100),(100,100),(-90,-90),(-90,-90),(-90,-90)]:
  before=call('_Z7JOY0DATv')
  call('zzuae_live_event',2,dx);call('zzuae_live_event',3,dy)
  call('_Z17devices_vsync_prev')
  after=call('_Z7JOY0DATv')
  assert ((after-before)&255)==(dx&255) and (((after>>8)-(before>>8))&255)==(dy&255),(dx,dy,hex(before),hex(after))
 print('PASS: mouse X/Y reach JOY0DAT across guest frames and counter wrap')
 call('zzuae_live_event',4,1);assert call(buttons,0,0)==0x80
 call('zzuae_live_event',7,0);assert call(buttons,0,0)==0xc0
 call('zzuae_live_event',6,4);assert call(buttons,0,0)==0x40
 call('zzuae_live_event',6,132);assert call(buttons,0,0)==0xc0
 # Button 2/3 reach real guest POTGOR pins, not just an input counter.
 for event,bit in [(5,0x4000),(6,0x1000)]:
  assert call('_Z6POTGORv')&bit
  call('zzuae_live_event',6,event);assert not(call('_Z6POTGORv')&bit)
  call('zzuae_live_event',6,event|128);assert call('_Z6POTGORv')&bit
 call('zzuae_live_event',6,5);call('zzuae_live_event',6,6)
 call('zzuae_live_event',7,0);assert call('_Z6POTGORv')&0x5000==0x5000
 joydir=next(v for k,v in sym.items() if k=='_ZL6joydir')
 for event,expected in [(0,2),(1,1),(2,4),(3,8)]:
  call('zzuae_live_event',6,event)
  assert struct.unpack('<I',u.mem_read(joydir+4,4))[0]==expected
  call('zzuae_live_event',6,event|128)
  assert struct.unpack('<I',u.mem_read(joydir+4,4))[0]==0
 print('PASS: three guest fire buttons, POTGOR pins, all directions and focus-loss release')
 # Backend write tests open a fresh image; release DF0 after the boot check
 # rather than allocating an unsupported third working disk on a 2 MiB guest.
 if df1_data is not None:call('_Z10disk_ejecti',0)
 scratch=base+0x483000;u.mem_write(scratch,b'wb12.adf\0r+b\0ZZZZ')
 opener='_Z11zfile_fopenPKcS0_i'
 assert call(opener,scratch,scratch+9,0)==0,'read-only image accepted write mode'
 original=bytes(u.mem_read(base+0x560000,16))
 u.mem_write(sym['uae_volatile_write'],struct.pack('<I',1))
 f=call(opener,scratch,scratch+9,0);assert f
 assert call('_Z12zfile_fwritePKvjjP5zfile',scratch+13,1,4,f)==4
 # AAPCS aligns the 64-bit seek offset to r2/r3; SEEK_SET is on the stack.
 assert call('_Z11zfile_fseekP5zfilexi',f,0,0,0,0)==0
 assert call('_Z11zfile_freadPvjjP5zfile',scratch+32,1,4,f)==4
 assert bytes(u.mem_read(scratch+32,4))==b'ZZZZ'
 call('_Z12zfile_fcloseP5zfile',f)
 assert bytes(u.mem_read(base+0x560000,16))==original,'staged disk image changed'
 print('PASS: volatile image write/read; original staged ADF unchanged')
 if df1_data is not None:
  import zlib
  assert struct.unpack('>I',u.mem_read(base+0x482864,4))[0]==zlib.crc32(df1_data)
  assert bytes(u.mem_read(sym['zzuae_disk1_image'],901120))==df1_data
  u.mem_write(scratch,b'df1.adf\0r+b\0ONE!')
  f=call(opener,scratch,scratch+8,0);assert f
  assert call('_Z12zfile_fwritePKvjjP5zfile',scratch+12,1,4,f)==4
  assert call('_Z11zfile_fseekP5zfilexi',f,0,0,0,0)==0
  assert call('_Z11zfile_freadPvjjP5zfile',scratch+32,1,4,f)==4
  assert bytes(u.mem_read(scratch+32,4))==b'ONE!'
  call('_Z12zfile_fcloseP5zfile',f)
  assert bytes(u.mem_read(sym['zzuae_disk1_image'],901120))==df1_data
  assert bytes(u.mem_read(base+0x560000,16))==original,'DF1 write changed DF0'
  u.mem_write(sym['uae_disk1_present'],bytes(4));assert not call(opener,scratch,scratch+8,0)
  print('PASS: actual DF1 insertion/CRC, independent volatile writes and absent-drive rejection')
 if audio:
  u.mem_write(sym['dmacon'],struct.pack('<H',0));call('_Z11audio_resetv')
 call('_Z6INTREQt',0x80)
 call('_Z7AUDxPERit',0,124)
 call('_Z7AUDxDATit',0,0x1234)
 assert struct.unpack('<H',u.mem_read(sym['intreq'],2))[0]&0x80,'Paula audio interrupt missing'
 print('PASS: Paula manual audio word raises channel interrupt after resetting DMA state')
 if '--direct-test' in sys.argv:
  address=0x003ff000;nonce=0x56ab1987
  if not direct_live:u.mem_map(0x00300000,0x300000)
  p=base+0x482c00;table=(base+0x400000+16383)&~16383
  colors=[0xf800,0x07e0,0x001f,0xffff,0,0x1234,0x89ab,0x5a5a]
  src=b''.join(struct.pack('<8H',*(colors[(x+y)%8] for x in range(8)))*80 for y in range(256))
  u.mem_write(pixels,src)
  for width,height in [(640,512),(640,480),(552,414),(320,240),(320,256)]:
   pitch=width*4+64;span=(height-1)*pitch+width*4
   for fmt in [3,4]:
    for mode in range(4):
     u.mem_write(address,b'\x55'*(span+32))
     u.mem_write(address,struct.pack('>I',nonce));u.mem_write(address+span-4,struct.pack('>I',nonce^0x31415926))
     u.mem_write(p+76,struct.pack('>8I',address,pitch,fmt,nonce,mode,1,width,height))
     assert call('zzuae_direct_convert')==0
     assert bytes(u.mem_read(base+0x490000,640*256*2))==src,'snapshot does not match held source frame'
     for y in range(height):
      sy=y*256//height
      level=8 # reserved old scanline field must not dim pixels
      row=bytearray()
      for x in range(width):
       c=colors[(x*640//width+sy)%8]
       r,g,b=c>>11,(c>>5)&63,c&31;r=(r<<3)|(r>>2);g=(g<<2)|(g>>4);b=(b<<3)|(b>>2)
       row.extend(v*level//8 for v in ([b,g,r,255] if fmt==3 else [255,r,g,b]))
      assert bytes(u.mem_read(address+y*pitch,width*4))==row,(width,fmt,mode,y)
      if y<height-1:assert bytes(u.mem_read(address+y*pitch+width*4,64))==b'\x55'*64
     assert bytes(u.mem_read(address+span,32))==b'\x55'*32
     for section in range(address>>20,(address+span-1>>20)+1):
      assert u.mem_read(table+section*4,4)==b'\0'*4,'mapping left installed'
  before=bytes(u.mem_read(address,span))
  for width_bad,height_bad in [(640,256),(0,0),(644,483),(316,237)]:
   u.mem_write(p+100,struct.pack('>2I',width_bad,height_bad))
   assert call('zzuae_direct_convert')==6
   assert bytes(u.mem_read(address,span))==before
  u.mem_write(p+100,struct.pack('>2I',width,height))
  print('PASS: PAL low/HiRes and three 4:3 sizes, both pixel formats, no software scanlines, source snapshots, invalid dimensions and row guards')
  # A failed ownership challenge must not alter the destination or retain mappings.
  before=bytes(u.mem_read(address,span))
  assert call('zzuae_direct_convert')==7
  assert bytes(u.mem_read(address,span))==before
  u.mem_write(table+(address>>20)*4,struct.pack('<I',0x12345))
  assert call('zzuae_direct_convert')==6
  assert u.mem_read(table+(address>>20)*4,4)==struct.pack('<I',0x12345)
  u.mem_write(table+(address>>20)*4,b'\0'*4)
  u.mem_write(address,struct.pack('>I',nonce));u.mem_write(address+span-4,struct.pack('>I',nonce^0x31415926))
  before=bytes(u.mem_read(address,span))
  u.mem_write(base+0x480010,bytes.fromhex('0100a0e31eff2fe1'))
  u.mem_write(sym['uae_stop'],struct.pack('<I',base+0x480010))
  assert call('zzuae_direct_convert')==2
  assert bytes(u.mem_read(address,span))==before
  for section in range(address>>20,(address+span-1>>20)+1):
   assert u.mem_read(table+section*4,4)==b'\0'*4,'cancel left mapping installed'
  print('PASS: actual ARM RGB565 conversion to both P96 formats; row padding; bounds; nonce rejection; mapping collision; cancellation and unmap')
  if '--neon' in sys.argv:
   assert neon_calls,'NEON path not exercised'
   if '--require-neon-half' in sys.argv:assert neon_half_calls,'320-pixel NEON path not exercised'
   assert all(u.reg_read(UC_ARM_REG_D0+i)==(0x123456789abcdef0^i) for i in range(32))
   assert u.reg_read(UC_ARM_REG_FPSCR)==0x01000000
   print('PASS: NEON direct path exercised; all D registers and FPSCR preserved')
if len(sys.argv)==1:
 result=struct.unpack('<11I',u.mem_read(base+0x480200,44))
 assert result[0]==100000 and result[2]==1000010 and result[3]==0x60000000 and result[7]==0x108,result
 assert u.mem_read(pixels,320*256*2)==b'\x00\xf8'*(320*256), 'OCS color output mismatch'
 print('PASS: upstream 68000/custom/CIA/event/drawing path, exact red RGB565 frame')

assert all(block_calls),block_calls
print('PASS mixed fetch modes, mid-line resolution and scroll writes; block calls',block_calls)
