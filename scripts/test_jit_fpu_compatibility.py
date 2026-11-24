#!/usr/bin/env python3
"""Bounded compatibility checks on explicitly selected recorded ARM payloads."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--jit',type=Path,required=True);p.add_argument('--fpu',type=Path,required=True);p.add_argument('--program',type=Path,required=True)
p.add_argument('--output',type=Path,default=Path('.context/jit-fpu-compatibility'));a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
record={'scope':'Cortex-A9 instruction model only; no physical cache, timing or gameplay claim','inputs':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.jit,a.fpu,a.program]},'checks':[]}
def run(label,script,args):
 command=[sys.executable,str(ROOT/'tests/amiga/uae4arm'/script),*map(str,args)]
 with (a.output/(label+'.log')).open('w') as log:subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
 record['checks'].append(label);(a.output/'results.json').write_text(json.dumps(record,indent=2)+'\n');print('PASS',label,flush=True)
for name,extra in [('implicit-smc',['--implicit-smc']),('cancel',['--cancel']),('fault',['--fault'])]:
 run(name,'jit_guest.py',['--elf',a.jit,'--cache32','--mmu',*extra])
for engine in [1,2]:
 for fpscr in ['0','0x00400000','0x00800000','0x03c09f00']:
  run(f'fpu-engine{engine}-fpscr{fpscr}','check_machine.py',[4,'--elf',a.fpu,'--cache32','--synthetic-rom','--profile',3,'--engine',engine,'--neon','--fpu-fixture','--fpu-program',a.program,'--host-fpscr',fpscr])
 run(f'fpu-off-engine{engine}','check_machine.py',[4,'--elf',a.fpu,'--cache32','--synthetic-rom','--profile',3,'--engine',engine,'--neon','--no-fpu-fixture'])
print('PASS',len(record['checks']),'compatibility configurations')
