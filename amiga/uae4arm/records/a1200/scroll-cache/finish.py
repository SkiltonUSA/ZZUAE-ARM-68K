from pathlib import Path
f=Path('.context/amiga/uae4arm/a1200/sprite-neon/finish.py')
s=f.read_text().replace('a1200/sprite-neon','a1200/scroll-cache').replace("('pixel4','sprite-neon')","('pixel4','scroll-cache')")
exec(compile(s,str(f),'exec'))
