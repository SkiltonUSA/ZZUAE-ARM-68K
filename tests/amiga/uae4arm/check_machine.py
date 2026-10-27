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
sym={p[2]:int(p[0],16)+base for line in subprocess.check_output(['/opt/homebrew/opt/llvm/bin/llvm-nm',elf],text=True).splitlines() if len(p:=line.split())==3}
u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
if '--trace-halt' in sys.argv:
 def halted(uc,*args):
  pc,pointer,origin=struct.unpack('<3I',uc.mem_read(sym['regs']+72,12))
  opcode=struct.unpack('<H',uc.mem_read(sym['regs']+84,2))[0]
  frame=struct.unpack('<I',uc.mem_read(sym['timeframes'],4))[0]
  print('GUEST_REGS', ['%08x'%v for v in struct.unpack('<16I',uc.mem_read(sym['regs'],64))],flush=True)
  raise RuntimeError('guest halt reason=%d pc=%08x opcode=%04x frame=%d' % (uc.reg_read(UC_ARM_REG_R0),(pc+pointer-origin)&0xffffffff,opcode,frame))
 u.hook_add(UC_HOOK_CODE,halted,begin=sym['_Z8cpu_halti'],end=sym['_Z8cpu_halti'])
neon_calls=[]
if '--neon' in sys.argv:
 u.reg_write(UC_ARM_REG_C1_C0_2,0xf00000);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
 for i in range(32):u.reg_write(UC_ARM_REG_D0+i,0x123456789abcdef0^i)
 u.reg_write(UC_ARM_REG_FPSCR,0x01000000)
 def cpacr(uc,address,*args):
  uc.reg_write(UC_ARM_REG_R1,uc.reg_read(UC_ARM_REG_C1_C0_2));uc.reg_write(UC_ARM_REG_PC,address+4)
 u.hook_add(UC_HOOK_CODE,cpacr,begin=sym['zu_neon_available'],end=sym['zu_neon_available'])
 def neon_call(*args):neon_calls.append(1)
 u.hook_add(UC_HOOK_CODE,neon_call,begin=sym['zu_convert_neon'],end=sym['zu_convert_neon'])
u.mem_map(base&~4095,block+8192);u.mem_write(base,bytes(image));u.mem_map(0xf8f00000,4096)
u.mem_write(base+0x480000,bytes.fromhex('0000a0e31eff2fe1'))
u.mem_write(sym['uae_shared'],struct.pack('<I',base))
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
 profile=int(sys.argv[sys.argv.index('--profile')+1]);assert 0<=profile<4
 u.mem_write(base+0x482814,struct.pack('>I',profile+1))
 expanded='--ram1m' in sys.argv
 if '--synthetic-rom' in sys.argv:
  rom=bytearray(524288 if profile>=2 else 262144)
  pc=0xf80040 if profile>=2 else 0xfc0040
  struct.pack_into('>II',rom,0,0x20000,pc)
  struct.pack_into('>HH',rom,12,37 if profile>=2 else 33 if profile==0 else 34,350 if profile==3 else 175)
  rom[64:]=bytes.fromhex('33fc0f0000dff18060fe')+rom[74:]
  u.mem_write(base+0x4e0000,bytes(rom))
 else:
  path=out/'media'/('kick12.rom' if profile==0 else 'kick13-clean.rom' if profile==1 else 'kick204.rom' if profile==2 else 'kick205.rom')
  u.mem_write(base+0x4e0000,path.read_bytes())
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
  program.extend(bytes.fromhex('60fe'))
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
if '--engine' in sys.argv:
 translated,fallback=struct.unpack('>2I',u.mem_read(base+0x482830,8))
 assert (translated>0) if engine==1 else (translated==0),(engine,translated)
 assert u.cpr_read(15,0,12,0,0,0,False)==0,'VBAR not restored'
 print('ENGINE',engine,'translated sites',translated,'fallback sites',fallback,flush=True)
if '--fpu-fixture' in sys.argv:
 chip=struct.unpack('<I',u.mem_read(sym['chipmem_bank']+32,4))[0]
 values=struct.unpack('>10I',u.mem_read(chip+0x10000,40))
 expected=(0,)*10 if '--fpu-off' in sys.argv else (16,4,0x40030000,0x80000000,0,2,3,2,4,0x46505531)
 assert values==expected,(values,expected)
 for i in range(32):assert u.reg_read(UC_ARM_REG_D0+i)==(0x123456789abcdef0^i),i
 assert u.reg_read(UC_ARM_REG_FPSCR)==0x01000000
 print('PASS: FPU Off rejects guest instructions' if '--fpu-off' in sys.argv else 'PASS: guest FPU arithmetic, sqrt, extended storage, directed rounding, ties-even and full VFP restoration',values)
if '--state-report' in sys.argv:
 # Pinned ARM ABI: addrbank.baseaddr follows eight 32-bit function pointers.
 # Compare guest RAM, register/CCR prefix (no native pointers), frame and PCM.
 chip=struct.unpack('<I',u.mem_read(sym['chipmem_bank']+32,4))[0]
 chip_size=struct.unpack('>I',u.mem_read(base+0x482808,4))[0]
 result=list(struct.unpack('<11I',u.mem_read(base+0x480200,44)))
 result[6]=0 # host timing is deliberately excluded
 digest=lambda address,size:hashlib.sha256(bytes(u.mem_read(address,size))).hexdigest()
 state={'result':result,'cpu_registers_ccr':digest(sym['regs'],72),
        'chip_ram':digest(chip,chip_size),'pixels':digest(base+0x490000,640*256*2),
        'pcm':hashlib.sha256(b''.join(pcm_blocks)).hexdigest()}
 Path(sys.argv[sys.argv.index('--state-report')+1]).write_text(json.dumps(state,indent=2)+'\n')
if '--ram1m' in sys.argv and profile is None:
 assert u.reg_read(UC_ARM_REG_R0)==0
 assert struct.unpack('>3I',u.mem_read(base+0x482808,12))==(524288,524288,1)
 print('PASS: mapped 512K Slow RAM full-bank pattern/alias test and clear')
if profile is not None:
 assert u.reg_read(UC_ARM_REG_R0)==0
 expected_chip=([0x40000,0x80000],[0x80000,0x80000],[0x100000,0x200000],[0x100000,0x200000])[profile][int(expanded)]
 expected_slow=0x80000 if profile==1 and expanded else 0
 assert struct.unpack('>3I',u.mem_read(base+0x482808,12))==(expected_chip,expected_slow,1)
 mask,compat,overlay=struct.unpack('>3I',u.mem_read(base+0x482818,12))
 assert mask==(3 if profile>=2 else 0),(profile,mask)
 assert compat==[8,5,6,7][profile] and overlay==(0 if profile==3 else 1)
 print('PASS: profile',profile,'Chip',expected_chip,'Slow',expected_slow,'chipset',mask,'overlay',overlay)
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
 # The normal UAE floppy LED callback publishes activity in ARM-owned status.
 for led,state,expected in [(1,1,1),(0,0,1),(1,3,1),(1,0,0)]:
  call('_Z7gui_lediii',led,state,0)
  assert struct.unpack('>I',u.mem_read(base+0x482c20,4))[0]==expected
 print('PASS: DF0 activity on/off and write state; unrelated LEDs leave it unchanged')
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
   assert all(u.reg_read(UC_ARM_REG_D0+i)==(0x123456789abcdef0^i) for i in range(32))
   assert u.reg_read(UC_ARM_REG_FPSCR)==0x01000000
   print('PASS: NEON direct path exercised; all D registers and FPSCR preserved')
if len(sys.argv)==1:
 result=struct.unpack('<11I',u.mem_read(base+0x480200,44))
 assert result[0]==100000 and result[2]==1000010 and result[3]==0x60000000 and result[7]==0x108,result
 assert u.mem_read(pixels,320*256*2)==b'\x00\xf8'*(320*256), 'OCS color output mismatch'
 print('PASS: upstream 68000/custom/CIA/event/drawing path, exact red RGB565 frame')
