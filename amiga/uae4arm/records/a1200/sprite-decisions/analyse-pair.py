from pathlib import Path
import re,json
p=Path('.context/amiga/uae4arm/a1200/sprite-decisions');g=p.parent/'gameplay';rows=[]
for v in ['pixel4','sprite-attachment']:
 f=g/f'banshee-demo-{v}-interpreter020-paula-6000-attachment-locked';log=(f/'run.log').read_text();d=json.loads((f/'metrics.json').read_text());d['variant']=v
 assert all(s in log for s in ['UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1','input_events=0'])
 d['state']=re.search(r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)',log).groups()
 d['pcm']=re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)',log).groups()
 assert d['pcm'][0]==d['pcm'][1]==d['pcm'][2]=='3330048'
 rows.append(d)
assert rows[0]['state']==rows[1]['state'] and rows[0]['pixels_sha256']==rows[1]['pixels_sha256']
gain=(rows[1]['mean_emulated_fps']/rows[0]['mean_emulated_fps']-1)*100
(p/'results.json').write_text(json.dumps({'runs':rows,'gain_percent':gain},indent=2)+'\n')
print('PASS matched guest state/pixels, PCM delivery and cleanup; gain',gain)
for d in rows:print(d['variant'],d['mean_emulated_fps'],'gaps',d['pcm'][-1])
