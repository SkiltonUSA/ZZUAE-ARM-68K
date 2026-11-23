from pathlib import Path
import json,re
p=Path(__file__).resolve().parent
for file in sorted(p.glob('*/metrics.json')):
 d=json.loads(file.read_text());log=(file.parent/'run.log').read_text()
 intervals=d.get('last_intervals_displayed_fps',d.get('last_intervals_fps',[]))
 tail= len(intervals)/sum(1/v for v in intervals) if intervals else 0
 cpu=re.search(r'UAE_MACHINE dispatches=(\d+).*? hash=(\w+) pc=(\w+)',log)
 print(file.parent.name, 'mean',round(d['mean_emulated_fps'],2),'late displayed',round(tail,2),'image',d['pixels_sha256'][:12],'cpu',cpu.groups() if cpu else None)
