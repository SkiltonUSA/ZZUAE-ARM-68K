from pathlib import Path
import re,json,sys
lab=Path(__file__).resolve().parent;out=lab/'hardware';rows=[]
for game in ['frontier','alien','wb20']:
 s=(out/f'service-{game}-{sys.argv[1] if len(sys.argv)>1 else "profilefinal"}-0.log').read_text()
 stages=[]
 for m in re.finditer(r'JIT_STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)',s):
  i,hi,lo,calls=map(int,m.groups());stages.append({'id':i,'ticks':(hi<<32)|lo,'calls':calls})
 assert len(stages)==7
 total=sum(t['ticks']for t in stages[:5]);special=stages[4]['ticks']
 for t in stages:t['percent_total']=100*t['ticks']/total
 rows.append({'workload':game,'elapsed_us':int(re.search(r'BOOT elapsed_us=(\d+)',s)[1]),'stages':stages,'stop_percent_special':100*stages[5]['ticks']/special,'copper_percent_special':100*stages[6]['ticks']/special})
(lab/'profile.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
