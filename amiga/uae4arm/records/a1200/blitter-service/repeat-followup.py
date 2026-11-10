from pathlib import Path
import time,subprocess,sys
p=Path('.context/amiga/uae4arm/a1200/blitter-service')
for i in range(180):
 s=(p/'candidate-repeat.log').read_text()
 if 'DONE banshee-demo-' in s:break
 if 'Traceback' in s:raise RuntimeError('candidate repeat failed; no following run')
 time.sleep(3)
else:raise RuntimeError('candidate repeat did not finish')
with (p/'reference-repeat.log').open('w') as log:subprocess.run([sys.executable,str(p/'run-reference-repeat.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
