from pathlib import Path
import sys, os

variant=sys.argv[1]
os.environ['ZZ_TEST_TAG']='-sprite-slots-locked'
f=Path('.context/amiga/uae4arm/a1200/gameplay/run.py')
s=f.read_text().replace("'OFF','6000'", "'PAULA','6000'")
sys.argv=[str(f),variant]
exec(compile(s,str(f),'exec'))
