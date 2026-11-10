from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parent
for variant in ('sprite-neon','pixel4'):
    with (p/(variant+'-repeat-hardware.log')).open('w') as log:
        subprocess.run([sys.executable,str(p/'run.py'),variant,'-sprite-neon-repeat-locked'],stdout=log,stderr=subprocess.STDOUT,check=True)
    print('PASS completed reverse-order run',variant,flush=True)
