from pathlib import Path
import re,json,sys
p=Path('.context/amiga/uae4arm/a1200/decision-costs');g=p.parent/'gameplay'
kind=sys.argv[1] if len(sys.argv)>1 else 'events'
variant,tag='decision-phases','decisions-locked'
f=g/f'banshee-demo-{variant}-interpreter020-paula-6000-{tag}'
r=g/'banshee-demo-pixel4-interpreter020-paula-6000-blitter-fast-reference-repeat'
s=(f/'run.log').read_text();ref=(r/'run.log').read_text()
signature=r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
assert re.search(signature,s).groups()==re.search(signature,ref).groups()
assert json.loads((f/'metrics.json').read_text())['pixels_sha256']==json.loads((r/'metrics.json').read_text())['pixels_sha256']
for marker in ('UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1','input_events=0','simd_errors=0'):assert marker in s,marker
pcm=re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)',s).groups();assert pcm[0]==pcm[1]==pcm[2]=='3330048'
hz=int(re.search(r'TIMER estimated_hz=(\d+)',s)[1])
names=['Finish decisions inclusive','Display-window decisions','Start/advance display line','Bitplane fetch decisions','Final fetch drain','Sprite decisions','Record line state','Empty timer calibration']
rows=[]
for stage,hi,lo,calls in re.findall(r'^STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)',s,re.M):
 ticks=(int(hi)<<32)|int(lo);calls=int(calls);assert calls
 rows.append(dict(stage=int(stage),name=names[int(stage)],samples=calls,ticks=ticks,estimated_seconds=ticks*64/hz,mean_ticks=ticks/calls))
assert rows
(p/(kind+'-stages.json')).write_text(json.dumps({'scope':'Sampled 1/64 calls at emulated frames >=3000; inclusive stages overlap and include waits; not an FPS comparison','audio_gaps':int(pcm[3]),'stages':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2));print('PASS matching guest state/pixels, PCM delivery and clean teardown')
