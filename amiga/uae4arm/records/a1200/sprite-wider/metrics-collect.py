from pathlib import Path
import shutil,json,re,hashlib
p=Path(__file__).resolve().parent;dest=Path('amiga/uae4arm/records/a1200/performance');dest.mkdir(exist_ok=True)
rows=[]
for file in sorted(p.glob('*/metrics.json')):
 label=file.parent.name
 if not (file.parent/'run.log').exists():continue
 log=(file.parent/'run.log').read_text();d=json.loads(file.read_text())
 d['name']=label
 intervals=d.get('last_intervals_displayed_fps',d.get('last_intervals_fps',[]));d['late_displayed_fps']=len(intervals)/sum(1/v for v in intervals) if intervals else None
 d['late_emulated_fps']=None
 draw=re.search(r'DRAW frames=(\d+) skipped=(\d+)',log)
 if draw:
  d['presented_frames'],d['skipped_frames']=map(int,draw.groups())
  if d['presented_frames']==d['frames'] and d['skipped_frames']==0:d['late_emulated_fps']=d['late_displayed_fps']
 d['clean_exit']=all(v in log for v in ('owned memory released','witness_bad=0','register_mismatches=00000000','failed=0'))
 d['command']=(file.parent/'command.txt').read_text().strip()
 rows.append(d)
 shutil.copy2(file.parent/'run.log',dest/(label+'.log'))
(dest/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
for name in ['product-model','product-fpu-model','neon320-after','chipreads-memory','scalar-memory','product-pal-window','product-pal-fullscreen','product-ntsc-window','product-ntsc-fullscreen','product-fpu-hardware','native','instruction-audit']:
 source=p/(name+'.log')
 if source.exists():shutil.copy2(source,dest/source.name)
for name in ['test-artifacts.json','installed-builds.json']:
 if (p/name).exists():shutil.copy2(p/name,dest/name)
print(len(rows),'recorded runs')

for source in p.glob('chip-product-*.log'):
 shutil.copy2(source,dest/source.name)
for name in ('installed-chip-builds.json','chip-fpu-model.log','copper-model.log'):
 if (p/name).exists():shutil.copy2(p/name,dest/name)
for folder in p.glob('*-navigation'):
 if (folder/'run.log').exists():shutil.copy2(folder/'run.log',dest/(folder.name+'.log'))
for source,name in [('slamdemo-navigation/3.png','slam-tilt-table.png'),('banshee-navigation/4.png','banshee-briefing.png')]:
 shutil.copy2(p/source,dest/name)
