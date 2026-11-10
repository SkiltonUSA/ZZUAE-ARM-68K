from pathlib import Path
import sys,subprocess,json
p=Path('.context/amiga/uae4arm/a1200/blitter-service');core=Path('tests/amiga/uae4arm/check_machine.py').resolve()
s=core.read_text();marker='u.reg_write(UC_ARM_REG_SP,base+block-4112);'
s=s.replace(marker,'''special_flags={}
def special_enter(uc,address,*args):
 flags=struct.unpack('<I',uc.mem_read(sym['regs']+100,4))[0]
 special_flags[flags]=special_flags.get(flags,0)+1
at=sym['_ZL14do_specialtiesi'];u.hook_add(UC_HOOK_CODE,special_enter,begin=at,end=at)
'''+marker,1)
s+='''
print('SPECIAL_FLAGS',special_flags)
for cost in (0,):
 u.mem_write(sym['regs']+100,struct.pack('<I',512))
 before=bytearray(u.mem_read(sym['regs'],128));struct.pack_into('<I',before,100,512)
 u.reg_write(UC_ARM_REG_R0,cost&0xffffffff)
 u.reg_write(UC_ARM_REG_SP,base+block-4112);u.reg_write(UC_ARM_REG_LR,base+0x480100)
 u.emu_start(sym['_ZL14do_specialtiesi'],base+0x480100,count=1000)
 assert u.reg_read(UC_ARM_REG_PC)==base+0x480100
 assert u.reg_read(UC_ARM_REG_R0)==0
 assert bytes(u.mem_read(sym['regs'],128))==bytes(before)
print('PASS actual ARM zero-cycle BLTNASTY-only service preserves flag and leaves other registers intact')
'''
w=p/'wrapper.py';w.write_text('import sys\nsys.path.insert(0,'+repr(str(core.parent))+')\n__file__='+repr(str(core))+'\n'+s)
for kind in (sys.argv[1:] or ('memory','irq','beam','colorwrite')):
 states=[]
 for variant in ('pixel4','blitter-flag-fast'):
  report=p/(kind+'-'+variant+'.json')
  args=[sys.executable,str(w),'4','--elf',str(p.parent/'gameplay'/('build-'+variant)/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--neon','--live','--state-report',str(report)]
  args+=['--copper-fixture' if kind=='colorwrite' else '--timing-fixture',kind]
  if kind=='colorwrite':args+=['--audio']
  with report.with_suffix('.log').open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
  states.append(json.loads(report.read_text()))
 assert states[0]==states[1],kind
 print('PASS',kind,'CPU/RAM/pixels/PCM equal',flush=True)
