from pathlib import Path
import struct,subprocess,sys,json
p=Path('.context/amiga/uae4arm/a1200/remaining');core=Path('tests/amiga/uae4arm/check_machine.py').resolve()
program=bytearray.fromhex('13fc000200bfe001')
def word(v,a):program.extend(struct.pack('>HHI',0x33fc,v,a))
for i in range(32):word((i*0x125)&0xfff,0xdff180+2*i)
for n in range(8):
 address=0x6000+n*0x1000
 for i,v in enumerate([0x4040+n*8,0x8000]+[v for row in range(64) for v in (0xa55a^(row*17),0xf00f^(row*5))]+[0,0]):word(v,address+2*i)
 word(address>>16,0xdff120+8*n);word(address&65535,0xdff122+8*n)
for v,a in [(0x2c81,0xdff08e),(0x2cc1,0xdff090),(0x38,0xdff092),(0xd0,0xdff094),(0,0xdff0e0),(0x5000,0xdff0e2),(0x1000,0xdff100),(0x8320,0xdff096)]:word(v,a)
program.extend(bytes.fromhex('60fe'))
s=core.read_text();addition=f'''
u.mem_write(base+0x4e0040,{bytes(program)!r})
sprite_eligible=[0]
def sprite_enter(uc,*args):
 sp=uc.reg_read(UC_ARM_REG_SP)
 dup,mask,collision=struct.unpack('<3I',uc.mem_read(sp,12))
 x=uc.reg_read(UC_ARM_REG_R0);x=x if x<0x80000000 else x-0x100000000
 low=struct.unpack('<i',uc.mem_read(sym['_ZL11sprite_minx'],4))[0]
 high=struct.unpack('<i',uc.mem_read(sym['_ZL11sprite_maxx'],4))[0]
 con3=struct.unpack('<I',uc.mem_read(sym['_ZL7bplcon3'],4))[0]
 if not collision and not mask and dup<=2 and ((con3&2) or (x>=low and x+(16<<dup)<=high)):sprite_eligible[0]+=1
at=sym['_ZL15record_sprite_1iPtmiijim']
u.hook_add(UC_HOOK_CODE,sprite_enter,begin=at,end=at)
'''
s=s.replace("if '--timing-fixture' in sys.argv:",addition+"\nif '--timing-fixture' in sys.argv:",1)
s+='''\nassert sprite_eligible[0]>0,sprite_eligible
print('PASS actual ARM sprite fixture eligible calls',sprite_eligible[0])
'''
wrapper=p/'sprite-arm-wrapper.py';wrapper.write_text(f'import sys\nsys.path.insert(0,{str(core.parent)!r})\n__file__={str(core)!r}\nexec(compile({s!r},__file__,"exec"),globals())\n')
reports=[]
for v in ('pixel4','sprite-plain'):
 tag='-ntsc' if '--ntsc' in sys.argv else ''
 report=p/f'sprite-arm-{v}{tag}.json'
 command=[sys.executable,str(wrapper),'4','--elf',str(p.parent/'gameplay'/('build-'+v)/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--neon','--live','--state-report',str(report)]
 if tag:command.append('--ntsc')
 with (p/f'sprite-arm-{v}{tag}.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
 reports.append(json.loads(report.read_text()))
assert reports[0]==reports[1]
print('PASS actual ARM sprite fixture: CPU, RAM, framebuffer and frame hashes match')
