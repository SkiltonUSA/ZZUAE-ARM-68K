from pathlib import Path
import re,json
p=Path('.context/amiga/uae4arm/a1200/sprite-decisions');g=p.parent/'gameplay'
log=(g/'banshee-demo-sprite-decision-profile-interpreter020-paula-6000-locked/run.log').read_text()
ref=(g/'banshee-demo-pixel4-interpreter020-paula-6000-sprite-repeat/run.log').read_text()
sig=r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
assert re.search(sig,log).groups()==re.search(sig,ref).groups()
assert all(x in log for x in ('UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1'))
names=['All sprite decisions','Display preparation','Candidate scan/sort','Record selected sprites','Sprite DMA','Nested pixel recorder']
hz=int(re.search(r'TIMER estimated_hz=(\d+)',log)[1]);rows=[]
for i,hi,lo,n in re.findall(r'^STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)',log,re.M):
 ticks=(int(hi)<<32)|int(lo);rows.append({'stage':int(i),'name':names[int(i)],'samples':int(n),'estimated_seconds':ticks*64/hz})
(p/'stages.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:print(row)
