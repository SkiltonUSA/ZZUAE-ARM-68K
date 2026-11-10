from pathlib import Path
import json,re
p=Path('.context/amiga/uae4arm/a1200/special-fast');g=p.parent/'gameplay'
f=g/'banshee-demo-special-counts-interpreter020-paula-6000-special-locked';r=g/'banshee-demo-pixel4-interpreter020-paula-6000-denise-locked'
s=(f/'run.log').read_text();ref=(r/'run.log').read_text();sig=r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
assert re.search(sig,s).groups()==re.search(sig,ref).groups()
assert json.loads((f/'metrics.json').read_text())['pixels_sha256']==json.loads((r/'metrics.json').read_text())['pixels_sha256']
for marker in ('UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1','input_events=0'):assert marker in s,marker
pcm=re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)',s).groups();assert pcm[0]==pcm[1]==pcm[2]=='3330048'
counts={int(i):int(n) for i,n in re.findall(r'^STAGE id=(\d+) ticks_hi=0 ticks_lo=0 calls=(\d+)',s,re.M)};assert len(counts)==6;assert sum(counts[i] for i in range(1,6))==counts[0]
names=['all','END_COMPILE only','BLTNASTY only','COPPER only','INT or DOINT only','other or combined']
r=[{'name':names[i],'calls':counts[i],'percent':100*counts[i]/counts[0]} for i in range(6)]
(p/'counts.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));print('PASS matched guest/pixels/PCM delivery and clean teardown; gaps',pcm[3])
