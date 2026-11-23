from pathlib import Path
p=Path('tests/amiga/uae4arm/check_machine.py')
s=p.read_text();needle='    for mode in range(4):\n'
assert s.count(needle)==1
s=s.replace(needle,needle+'''     # Alternate cache hits with changed source colours at fixed dimensions.
     if mode&1:colors=[c^0x0841 for c in colors]
     src=b''.join(struct.pack('<8H',*(colors[(x+y)%8] for x in range(8)))*80 for y in range(256))
     u.mem_write(pixels,src)
''')
exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p.resolve())})
