from pathlib import Path
import re,json,sys
labels=['dispatch/bookkeeping','validation','handler (including cold learning)','interpreter fallback','interrupt/special handling']
records=[]
for name in sys.argv[1:]:
 p=Path(name);text=p.read_text()
 total,samples=map(int,re.search(r'JIT_PROFILE dispatches=(\d+) samples=(\d+)',text).groups())
 stages=[]
 for match in re.finditer(r'JIT_STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)',text):
  i,hi,lo,calls=map(int,match.groups());stages.append(dict(stage=labels[i],id=i,ticks=(hi<<32)|lo,calls=calls))
 assert len(stages)==5
 sum_ticks=sum(s['ticks']for s in stages)
 for s in stages:s['sampled_share_percent']=100*s['ticks']/sum_ticks
 records.append(dict(log=p.name,dispatches=total,samples=samples,elapsed_us=int(re.search(r'BOOT elapsed_us=(\d+)',text)[1]),stages=stages))
print(json.dumps(records,indent=2))
