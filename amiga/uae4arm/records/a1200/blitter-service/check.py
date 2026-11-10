from pathlib import Path
import subprocess,sys,json
p=Path('.context/amiga/uae4arm/a1200/blitter-service');g=p.parent/'gameplay'
for fixture in ('bits3-pal','copper3-pal'):
 states=[]
 for variant in ('pixel4','blitter-service'):
  tag=fixture+'-'+variant
  args=[sys.executable,'tests/amiga/uae4arm/check_machine.py','16','--elf',str(g/('build-'+variant)/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--rom',str(p.parent/'aga-events'/(fixture+'.rom')),'--neon','--direct-live','--state-report',str(p/(tag+'.json'))]
  with (p/(tag+'.log')).open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
  states.append(json.loads((p/(tag+'.json')).read_text()))
 assert states[0]==states[1],fixture
 print('PASS',fixture,'profile build matches reference; warm-up counters inactive',flush=True)
