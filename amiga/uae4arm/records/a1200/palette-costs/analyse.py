from pathlib import Path
import json,re
p=Path('.context/amiga/uae4arm/a1200/palette-costs');g=p.parent/'gameplay'
f=g/'banshee-demo-palette-profile-interpreter020-paula-6000-palette-locked'
r=g/'banshee-demo-pixel4-interpreter020-paula-6000-denise-locked'
s=(f/'run.log').read_text();ref=(r/'run.log').read_text()
signature=r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
assert re.search(signature,s).groups()==re.search(signature,ref).groups()
assert json.loads((f/'metrics.json').read_text())['pixels_sha256']==json.loads((r/'metrics.json').read_text())['pixels_sha256']
for token in ('UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1','input_events=0'):assert token in s,token
pcm=re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)',s).groups();assert pcm[0]==pcm[1]==pcm[2]=='3330048'
hz=int(re.search(r'TIMER estimated_hz=(\d+)',s)[1]);names=['remember_ctable inclusive','recorded palette copy','adjust_drawing_colors inclusive','drawing palette copy','line reset clears','empty timer calibration']
rows=[]
for stage,hi,lo,calls in re.findall(r'^STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)',s,re.M):
 ticks=(int(hi)<<32)|int(lo);calls=int(calls);assert calls
 rows.append(dict(stage=int(stage),name=names[int(stage)],samples=calls,ticks=ticks,estimated_seconds=ticks*64/hz,mean_ticks=ticks/calls))
assert len(rows)==6
(p/'stages.json').write_text(json.dumps({'scope':'Sampled 1/64 calls at emulated frames >=3000; inclusive stages overlap; not an FPS comparison','audio_gaps':int(pcm[3]),'stages':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2));print('PASS matched guest state/pixels and PCM sample delivery; clean teardown')
