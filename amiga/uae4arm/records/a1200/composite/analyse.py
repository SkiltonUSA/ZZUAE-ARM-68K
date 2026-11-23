from pathlib import Path
import re,json
p=Path(__file__).resolve().parent.parent/'gameplay'
folder=p/'banshee-demo-composite-profile-interpreter020-off-6000'
s=(folder/'run.log').read_text()
hz=int(re.search(r'TIMER estimated_hz=(\d+)',s)[1])
progress=dict((int(a),int(b)) for a,b in re.findall(r'PROGRESS frames=(\d+) elapsed_us=(\d+)',s))
seconds=(progress[6000]-progress[3000])/1e6
names=['draw_line','planar_to_chunky','palette_cache','sprite_composition','colour_changes','palette_pixels']
stages=[]
for i,hi,lo,calls in re.findall(r'STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)',s):
 ticks=(int(hi)<<32)+int(lo);t=ticks*64/hz
 stages.append(dict(name=names[int(i)],samples=int(calls),estimated_seconds=t,estimated_inclusive_percent=t/seconds*100))
labels=['lines','border_lines','sprite_lines','colour_change_lines','colour_changes','palette_full_copy','palette_rgb_copy','palette_cached','pixel_spans','destination_pixels','aga_stretch','aga_normal','aga_shrink','other_worker','ham_spans','dualpf_spans','ehb_spans','normal_spans','ham_pixels','dualpf_pixels','ehb_pixels','normal_pixels','identity_xor_mask']
counts={labels[int(i)]:int(v) for i,v in re.findall(r'COMPOSITE_COUNT id=(\d+) value=(\d+)',s) if int(i)<len(labels)}
assert counts['pixel_spans']==sum(counts[x] for x in ['ham_spans','dualpf_spans','ehb_spans','normal_spans'])
r=dict(gameplay_seconds=seconds,stages=stages,counts=counts)
(folder/'composite-analysis.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
