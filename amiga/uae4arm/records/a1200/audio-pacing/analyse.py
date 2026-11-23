from pathlib import Path
import json,re,sys
p=Path(__file__).resolve().parent;variant=sys.argv[1];frames=2048 if variant=='audio-2048' else 1024
f=p.parent/'gameplay'/f'banshee-demo-{variant}-interpreter020-paula-6000'
s=(f/'run.log').read_text();m=json.loads((f/'metrics.json').read_text())
fields=lambda line:{k:int(v) for k,v in re.findall(r'(\w+)=(\d+)',line)}
hz=int(re.search(r'TIMER estimated_hz=(\d+)',s)[1]);rate=int(re.search(r'AUDIO_PCM .*rate=(\d+)',s)[1])
rows=[]
for line in re.findall(r'AUDIO_PRODUCER (.*)',s):
 t=fields(line);seconds=((t['span_hi']<<32)+t['span_lo'])/hz
 t.update(interval_seconds=seconds,average_block_ms=seconds*1000/t['intervals'],block_duration_ms=1000*frames/rate,max_block_ms=t['max_ticks']*1000/hz,full_queue_wait_seconds=((t['wait_hi']<<32)+t['wait_lo'])/hz,production_to_playback_ratio=(t['intervals']*frames/rate)/seconds)
 rows.append(t)
service=fields(re.search(r'AUDIO_SERVICE (.*)',s)[1]);task=fields(re.search(r'AUDIO_TASK (.*)',s)[1]);live=fields(re.search(r'LIVE (.*)',s)[1])
assert task['queued']==task['submitted']==task['completed'] and task['error']==0
for key in ['owned memory released','witness_bad=0','register_mismatches=00000000','failed=0']:assert key in s,key
r={'variant':variant,'frames_per_block':frames,'rate':rate,'metrics':m,'producer':rows,'service':service,'device':task,'display':live,'audio_seconds':task['completed']/rate,'wall_seconds':m['elapsed_us']/1e6}
r['audio_shortfall_seconds']=r['wall_seconds']-r['audio_seconds']
(p/f'{variant}-analysis.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
