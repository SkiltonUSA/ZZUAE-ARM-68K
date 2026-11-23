from pathlib import Path
import re,json
p=Path('.context/amiga/uae4arm/a1200/bitplane-spans');g=p.parent/'gameplay';rows=[]
for v in ['pixel4','denise-once','fetch-outline','fetch-table']:
 f=g/f'banshee-demo-{v}-interpreter020-paula-6000-denise-locked';log=(f/'run.log').read_text();d=json.loads((f/'metrics.json').read_text());d['variant']=v
 assert all(s in log for s in ['UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1','input_events=0'])
 d['state']=re.search(r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)',log).groups()
 d['pcm']=re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)',log).groups()
 assert d['pcm'][0]==d['pcm'][1]==d['pcm'][2]=='3330048'
 if rows:assert d['state']==rows[0]['state'] and d['pixels_sha256']==rows[0]['pixels_sha256']
 d['change_percent']=(d['mean_emulated_fps']/(rows[0]['mean_emulated_fps'] if rows else d['mean_emulated_fps'])-1)*100
 rows.append(d)
(p/'all-results.json').write_text(json.dumps(rows,indent=2)+'\n')
for d in rows:print(d['variant'],d['mean_emulated_fps'],'change',d['change_percent'],'gaps',d['pcm'][-1])
print('PASS matched state/pixels, PCM delivery and cleanup')
