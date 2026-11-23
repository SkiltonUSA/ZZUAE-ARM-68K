from pathlib import Path
import sys,subprocess,json
p=Path(__file__).resolve().parent;g=p.parent/'gameplay';variant=sys.argv[1];frames=int(sys.argv[2]) if len(sys.argv)>2 else 1024
source=Path('tests/amiga/uae4arm/check_machine.py').resolve()
# Only the model consumer's PCM block size changes; production wire stays bounded.
s=source.read_text().replace('(r%4)*4096,4096',f'(r%4)*{frames*4},{frames*4}')
wrapper=p/f'model-{variant}.py'
wrapper.write_text('import sys\n'+f'exec(compile({s!r},{str(source)!r},"exec"),{{"__file__":{str(source)!r},"__name__":"__main__"}})\n')
for name in ['pixel4',variant]:
 script=source if name=='pixel4' else wrapper
 report=p/f'{variant}-{name}.json'
 cmd=[sys.executable,str(script),'10','--elf',str(g/('build-'+name)/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--synthetic-rom','--neon','--live','--audio','--state-report',str(report)]
 with (p/f'{variant}-{name}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
a=json.loads((p/f'{variant}-pixel4.json').read_text());b=json.loads((p/f'{variant}-{variant}.json').read_text());assert a==b,(a,b)
print('PASS',variant,'guest CPU, RAM, pixels and PCM match reference')
