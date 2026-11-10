from pathlib import Path
import struct,subprocess,sys,json
p=Path('.context/amiga/uae4arm/a1200/scroll-cache');core=Path('tests/amiga/uae4arm/check_machine.py').resolve()
program=bytearray.fromhex('13fc000200bfe001')
def word(v,a):program.extend(struct.pack('>HHI',0x33fc,v,a))
for i in range(32):word((i*0x125)&0xfff,0xdff180+2*i)
for i in range(256):word((0xa55a^(i*73))&65535,0x5000+2*i)
for n in range(4):word(0,0xdff0e0+4*n);word(0x5000,0xdff0e2+4*n)
copper=[]
for y in range(48,225,16):
 for i,(x,mode,con) in enumerate([(0x30,0,0x4000),(0x70,1,0xc000),(0xb0,3,0x2040)]):
  copper.extend([y*256+x+1,0xfffe,0x1fc,mode,0x100,con,0x102,(y*19+i*0x135)&65535,0x180,(y*13+x*23)&0xfff])
  if '--boundaries' in sys.argv and (y//16)%2==0:
   copper.extend([(0x094,0x0d0,0x096,0x8100),(0x094,0x048,0x096,0x0100),(0x094,0x0d0,0x096,0x8100)][i])
copper.extend([0xffff,0xfffe])
for i,v in enumerate(copper):word(v,0x3000+2*i)
for v,a in [(0x2c81,0xdff08e),(0x2cc1,0xdff090),(0x38,0xdff092),(0xd0,0xdff094),(0x4000,0xdff100),(0,0xdff080),(0x3000,0xdff082),(0x8380,0xdff096),(0,0xdff088)]:word(v,a)
program.extend(bytes.fromhex('60fe'))
s=core.read_text();marker='u.reg_write(UC_ARM_REG_SP,base+block-4112)'
addition=f'''u.mem_write(base+0x4e0040,{bytes(program)!r})
block_calls=[0,0,0]
def block_enter(uc,address,*args):
 for i in range(3):
  if address==sym['_ZL26beginning_of_plane_block_%di'%i]:block_calls[i]+=1
for i in range(3):
 at=sym['_ZL26beginning_of_plane_block_%di'%i]
 u.hook_add(UC_HOOK_CODE,block_enter,begin=at,end=at)
'''
s=s.replace(marker,addition+marker,1)
s+='''\nassert all(block_calls),block_calls
print('PASS mixed fetch modes, mid-line resolution and scroll writes; block calls',block_calls)
'''
wrapper=p/('mixed-arm-wrapper'+('-ntsc' if '--ntsc' in sys.argv else '-pal')+('-boundaries' if '--boundaries' in sys.argv else '')+'.py');wrapper.write_text(f'import sys\nsys.path.insert(0,{str(core.parent)!r})\n__file__={str(core)!r}\n'+s)
reports=[]
variant=sys.argv[sys.argv.index('--variant')+1] if '--variant' in sys.argv else 'scroll-cache'
for v in ('pixel4',variant):
 tag=('-ntsc' if '--ntsc' in sys.argv else '')+('-boundaries' if '--boundaries' in sys.argv else '')
 report=p/f'mixed-{v}{tag}.json'
 command=[sys.executable,str(wrapper),'5','--elf',str(p.parent/'gameplay'/('build-'+v)/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--neon','--live','--state-report',str(report)]
 if '--ntsc' in sys.argv:command.append('--ntsc')
 with (p/f'mixed-{v}{tag}.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
 reports.append(json.loads(report.read_text()))
assert reports[0]==reports[1],[(k,reports[0][k],reports[1][k]) for k in reports[0] if reports[0][k]!=reports[1][k]]
print('PASS mixed-mode reference/candidate CPU, RAM, pixels and frame hashes')
