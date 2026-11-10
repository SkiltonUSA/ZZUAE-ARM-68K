from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parent
with (p/'reference-run.log').open('w') as log:
 subprocess.run([sys.executable,str(p/'run.py'),'pixel4'],stdout=log,stderr=subprocess.STDOUT,check=True)
