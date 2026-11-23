from pathlib import Path
import subprocess,sys,json
p=Path('.context/amiga/uae4arm/a1200/gameplay').resolve();ref=p/'build-pixel4/uae-machine.elf';variant=sys.argv[1] if len(sys.argv)>1 else 'eventfast';candidate=p/('build-'+variant)/'uae-machine.elf'
for kind in ('memory','irq','beam','colorwrite'):
 states=[]
 for label,elf in [('reference',ref),('candidate',candidate)]:
  report=p/((variant+'-' if variant!='eventfast' else '')+kind+'-'+label+'.json')
  cmd=[sys.executable,'tests/amiga/uae4arm/check_machine.py','3','--elf',str(elf),'--cache32','--engine','2','--profile','4','--synthetic-rom','--neon','--live','--state-report',str(report)]
  cmd+=['--copper-fixture' if kind=='colorwrite' else '--timing-fixture',kind]
  with report.with_suffix('.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
  states.append(json.loads(report.read_text()))
 assert states[0]==states[1],(kind,[k for k in states[0] if states[0][k]!=states[1][k]])
 print('PASS',kind,'CPU, RAM, pixels and frame hashes match',flush=True)
