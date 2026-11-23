from pathlib import Path
import subprocess,os
p=Path('.context/amiga/uae4arm/a1200/bitplane-spans')
for variant in ('pixel4','denise-once'):
 if variant=='denise-once':
  assert (p/'denise-model.log').read_text().count('PASS')==4
  for f in ('mixed-arm.log','mixed-arm-ntsc.log'):
   assert 'PASS mixed-mode reference/candidate' in (p/f).read_text()
 with (p/(variant+'-run.log')).open('w') as log:
  subprocess.run(['.tools/amiga-venv/bin/python','.context/amiga/uae4arm/a1200/idle-fetch/run.py',variant,'PAULA','6000'],env={**os.environ,'ZZ_TEST_TAG':'-denise-locked'},stdout=log,stderr=subprocess.STDOUT,check=True)
 print('DONE',variant,flush=True)
