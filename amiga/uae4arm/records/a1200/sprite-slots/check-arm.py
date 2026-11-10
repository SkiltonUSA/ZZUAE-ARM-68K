from pathlib import Path
import sys

p=Path(__file__).resolve().parent
# Reuse the existing actual-ARM sprite fixture, changing only output location
# and tested binary. It asserts that attached sprite rendering is exercised.
f=p.parent/'sprite-decisions/attachment-arm.py'
s=f.read_text().replace("p=Path('.context/amiga/uae4arm/a1200/sprite-decisions')",
                       "p=Path('.context/amiga/uae4arm/a1200/sprite-slots')")
s=s.replace("'sprite-attachment'", "'sprite-slots'")
exec(compile(s,str(f),'exec'))
