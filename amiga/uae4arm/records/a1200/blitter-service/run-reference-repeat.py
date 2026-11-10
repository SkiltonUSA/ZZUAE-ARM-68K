from pathlib import Path
import sys,os
os.environ['ZZ_TEST_TAG']='-blitter-fast-reference-repeat'
f=Path('.context/amiga/uae4arm/a1200/gameplay/run.py')
s=f.read_text().replace("'OFF','6000'","'PAULA','6000'")
sys.argv=[str(f),'pixel4'];exec(compile(s,str(f),'exec'))
