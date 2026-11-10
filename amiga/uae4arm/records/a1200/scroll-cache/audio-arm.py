from pathlib import Path
import subprocess,sys,json
p=Path('.context/amiga/uae4arm/a1200/scroll-cache');reports=[]
variant=sys.argv[sys.argv.index('--variant')+1] if '--variant' in sys.argv else 'scroll-cache'
for v in ['pixel4',variant]:
 report=p/('audio-'+v+'.json')
 cmd=[sys.executable,'tests/amiga/uae4arm/check_machine.py','4','--elf',str(p.parent/'gameplay'/('build-'+v)/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--neon','--live','--audio','--copper-fixture','colorwrite','--state-report',str(report)]
 with (p/('audio-'+v+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 reports.append(json.loads(report.read_text()))
assert reports[0]==reports[1]
assert reports[0]['pcm']!='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
print('PASS CPU/RAM/pixels and nonempty PCM hashes match')
