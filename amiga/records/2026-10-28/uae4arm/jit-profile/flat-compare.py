from pathlib import Path
import json,re,statistics
lab=Path(__file__).resolve().parent;out=lab.parent/'next-pass';rows=[]
for game in ['frontier','alien','wb20']:
 record={'workload':game};states=[]
 for mode in ['baseline','flat']:
  records=[]
  for suffix in (['-r1','-r2'] if mode=='baseline' else ['','-r1']):
   p=out/('profile-'+game+'-'+mode+suffix+'.log');text=p.read_text()
   state=re.search(r'cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)',text).groups();states.append(state)
   records.append({'log':p.name,'elapsed_us':int(re.search(r'BOOT elapsed_us=(\d+)',text)[1])})
  record[mode]=records;record[mode+'_mean_us']=statistics.mean(r['elapsed_us']for r in records)
 assert len(set(states))==1
 record['state']=dict(zip(['cycles','hash','pc','frames'],states[0]))
 record['throughput_percent']=100*(record['baseline_mean_us']/record['flat_mean_us']-1)
 rows.append(record)
print(json.dumps(rows,indent=2))
(lab/'flat-comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
