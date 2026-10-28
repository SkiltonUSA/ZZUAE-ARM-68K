from pathlib import Path
import subprocess
root=Path.cwd();lab=root/'.context/amiga/uae4arm/jit-profile'
for mode,repeat in [('flat',0),('flat',1),('baseline',2)]:
 with (lab/(mode+'-r'+str(repeat)+'.log')).open('w')as out:
  subprocess.run([str(root/'.tools/amiga-venv/bin/python'),str(lab/'run.py'),mode,str(repeat),str(1 if mode=='flat' and repeat==0 else 0)],stdout=out,stderr=subprocess.STDOUT,check=True)
 print('PASS',mode,repeat,flush=True)
