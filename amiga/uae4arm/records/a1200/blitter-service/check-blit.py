from pathlib import Path
import sys,struct,subprocess,json
p=Path('.context/amiga/uae4arm/a1200/blitter-service');core=Path('tests/amiga/uae4arm/check_machine.py').resolve()
code=bytearray.fromhex('13fc000200bfe001')
for value,addr in [(0x01ff,0xdff040),(0,0xdff042),(0,0xdff054),(0x8000,0xdff056),(0,0xdff066),(0x8640,0xdff096),(0x1920,0xdff058)]:code.extend(struct.pack('>HHI',0x33fc,value,addr))
code.extend(bytes.fromhex('60fe'))
s=core.read_text();marker='u.reg_write(UC_ARM_REG_SP,base+block-4112);'
s=s.replace(marker,f'''u.mem_write(base+0x4e0040,{bytes(code)!r})
sole=[0]
def count(uc,address,*args):
 if struct.unpack('<I',uc.mem_read(sym['regs']+100,4))[0]==512:sole[0]+=1
at=sym['_ZL14do_specialtiesi'];u.hook_add(UC_HOOK_CODE,count,begin=at,end=at)
'''+marker,1)
s+='\nprint("BLITTER_ONLY_CALLS",sole[0])\nassert (sole[0]>0) if "build-pixel4" in str(elf) else sole[0]==0\n'
w=p/'blitter-wrapper.py';w.write_text('import sys\nsys.path.insert(0,'+repr(str(core.parent))+')\n__file__='+repr(str(core))+'\n'+s)
states=[]
for v in ('pixel4','blitter-flag-fast'):
 report=p/('blitter-'+v+'.json')
 args=[sys.executable,str(w),'4','--elf',str(p.parent/'gameplay'/('build-'+v)/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--neon','--live','--state-report',str(report)]
 with report.with_suffix('.log').open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
 states.append(json.loads(report.read_text()))
assert states[0]==states[1]
print('PASS blitter guest CPU/RAM/pixels equal; reference calls proven, candidate skips them')
