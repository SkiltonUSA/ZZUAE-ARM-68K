from pathlib import Path
import sys

p=Path(__file__).resolve().parent
f=p.parent/'sprite-decisions/attachment-arm.py'
s=f.read_text().replace("p=Path('.context/amiga/uae4arm/a1200/sprite-decisions')",
                       "p=Path('.context/amiga/uae4arm/a1200/sprite-neon')")
s=s.replace("'sprite-attachment'", "'sprite-neon'")
needle="wrapper=p/'sprite-arm-wrapper.py'"
control='''
s += "\\nif 'zu_sprite_neon_spans' in sym:\\n count=struct.unpack('<I',u.mem_read(sym['zu_sprite_neon_spans'],4))[0]\\n assert (count>0) if '--neon' in sys.argv else (count==0),count\\n print('PASS actual candidate NEON spans',count)\\n"
'''
s=s.replace(needle,control+needle)
if '--disabled' in sys.argv:
    s=s.replace("'--neon',",'')
    s=s.replace("tag='-ntsc' if '--ntsc' in sys.argv else ''", "tag='-disabled'")
    s=s.replace("if tag:command.append('--ntsc')", "if '--ntsc' in sys.argv:command.append('--ntsc')")
exec(compile(s,str(f),'exec'))
