import os,subprocess
from pathlib import Path
p=Path('.context/amiga/uae4arm/a1200/remaining')
for v in ('sprite-plain','pixel4'):
 with (p/(v+'-repeat-run.log')).open('w') as log:
  subprocess.run(['.tools/amiga-venv/bin/python','.context/amiga/uae4arm/a1200/idle-fetch/run.py',v,'PAULA','6000'],env={**os.environ,'ZZ_TEST_TAG':'-sprite-repeat'},stdout=log,stderr=subprocess.STDOUT,check=True)
 print('DONE',v,flush=True)
