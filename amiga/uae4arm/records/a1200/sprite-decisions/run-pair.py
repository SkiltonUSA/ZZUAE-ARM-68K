from pathlib import Path
import subprocess,os
p=Path('.context/amiga/uae4arm/a1200/sprite-decisions')
for variant in ('pixel4','sprite-attachment'):
 if variant=='sprite-attachment':
  assert (p/'attachment-model.log').read_text().count('PASS')==4
  for f in ('attachment-arm.log','attachment-arm-ntsc.log'):
   assert 'PASS actual ARM sprite fixture:' in (p/f).read_text()
 with (p/(variant+'-run.log')).open('w') as log:
  subprocess.run(['.tools/amiga-venv/bin/python','.context/amiga/uae4arm/a1200/idle-fetch/run.py',variant,'PAULA','6000'],env={**os.environ,'ZZ_TEST_TAG':'-attachment-locked'},stdout=log,stderr=subprocess.STDOUT,check=True)
 print('DONE',variant,flush=True)
