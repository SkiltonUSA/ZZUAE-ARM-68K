from pathlib import Path
import re,json
p=Path('.context/amiga/uae4arm/a1200/bitplane-spans');g=p.parent/'gameplay'
folder=g/'banshee-demo-bitplane-span-profile-interpreter020-paula-6000-spans-locked';log=(folder/'run.log').read_text()
ref=(g/'banshee-demo-pixel4-interpreter020-paula-6000-attachment-locked/run.log').read_text()
sig=r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
assert re.search(sig,log).groups()==re.search(sig,ref).groups()
assert all(s in log for s in ['UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1','input_events=0'])
names=['Whole update_fetch','Preparation loop','Bulk do_long_fetch','Trailing cycle loop','Nested block setup','Nested final shifter drain']
hz=int(re.search(r'TIMER estimated_hz=(\d+)',log)[1]);rows=[]
for i,hi,lo,n in re.findall(r'^STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)',log,re.M):
 ticks=(int(hi)<<32)|int(lo);rows.append({'stage':int(i),'name':names[int(i)],'samples':int(n),'estimated_seconds':ticks*64/hz})
(p/'stages.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:print(row)
