from pathlib import Path
import subprocess,sys,json
p=Path('.context/amiga/uae4arm/a1200/buffer-audit')
for label,rom in [('bits','bits3-pal.rom'),('copper','copper3-pal.rom')]:
 states=[]
 for enabled in (False,True):
  tag=label+('-profile' if enabled else '-reference')
  command=[sys.executable,'tests/amiga/uae4arm/check_machine.py','16','--elf',str(p.parent/'gameplay/build-pixel4/uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--rom',str(p.parent/'aga-events'/rom),'--neon','--live','--state-report',str(p/(tag+'.json'))]
  if enabled:command+=['--buffer-report',str(p/(label+'-buffers.json'))]
  with (p/(tag+'.log')).open('w')as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
  states.append(json.loads((p/(tag+'.json')).read_text()))
 assert states[0]==states[1],label
 print('PASS',label,'buffer hooks preserve CPU/RAM/pixels/result',flush=True)
