from pathlib import Path
import json,re,sys
p=Path('.context/amiga/uae4arm/a1200/blitter-wider');g=p.parent/'gameplay'
kind=sys.argv[1]
if kind=='intro':
 names=['slamdemo-'+v+'-interpreter020-paula-6000-blitter-wider' for v in ('pixel4','blitter-flag-fast')];pcm='3330048'
else:
 names=['slamdemo-blit-table-'+v+'-interpreter020-paula-9000-blit-table' for v in ('reference','candidate')];pcm='4995072'
rows=[]
for name in names:
 f=g/name;log=(f/'run.log').read_text();row=json.loads((f/'metrics.json').read_text())
 for marker in ('UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1','input_events=0'):
  assert marker in log,marker
 row['state']=re.search(r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)',log).groups()
 row['pcm']=re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)',log).groups()
 assert row['pcm'][0]==row['pcm'][1]==row['pcm'][2]==pcm
 row['name']=name;rows.append(row)
assert rows[0]['state']==rows[1]['state']
assert rows[0]['pixels_sha256']==rows[1]['pixels_sha256']
out={'runs':rows,'gain_percent':100*(rows[1]['mean_emulated_fps']/rows[0]['mean_emulated_fps']-1)}
(p/(kind+'-results.json')).write_text(json.dumps(out,indent=2)+'\n')
print(kind,'PASS matching guest state, pixels, PCM delivery, restore and release',flush=True)
print('FPS',*[x['mean_emulated_fps'] for x in rows],'gain',out['gain_percent'],flush=True)
