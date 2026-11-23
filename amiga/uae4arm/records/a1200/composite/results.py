from pathlib import Path
import re,json,shutil
p=Path(__file__).resolve().parent.parent/'gameplay'
d=Path('amiga/uae4arm/records/a1200/composite')
rows=[]
for label,name in [('reference-earlier','reference'),('candidate-first','pixel4'),('reference-fresh','reference'),('candidate-repeat','pixel4')]:
 tag={'reference-fresh':'composite-control','candidate-repeat':'composite-repeat'}.get(label,'')
 f=p/f'banshee-demo-{name}-interpreter020-off-6000{tag}'
 s=(f/'run.log').read_text();m=json.loads((f/'metrics.json').read_text())
 progress={int(a):int(b) for a,b in re.findall(r'PROGRESS frames=(\d+) elapsed_us=(\d+)',s)}
 assert m['frames']==6000
 assert m['pixels_sha256']=='78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e'
 for marker in ['dispatches=116472634 cycles=814003022 hash=eef62420 pc=00029056 frames=6000','register_mismatches=00000000','witness_bad=0','failed=0','owned memory released']:assert marker in s,(label,marker)
 rows.append(dict(label=label,whole_fps=m['mean_emulated_fps'],gameplay_fps=3000e6/(progress[6000]-progress[3000]),pixels_sha256=m['pixels_sha256']))
 for file in ['command.txt','run.log','metrics.json']:shutil.copy2(f/file,d/(label+'-'+file))
r=dict(runs=rows,first_gain_percent=(rows[1]['gameplay_fps']/rows[0]['gameplay_fps']-1)*100,repeat_gain_percent=(rows[3]['gameplay_fps']/rows[2]['gameplay_fps']-1)*100)
(d/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
