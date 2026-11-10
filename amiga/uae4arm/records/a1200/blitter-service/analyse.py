from pathlib import Path
import re,json
p=Path('.context/amiga/uae4arm/a1200/blitter-service');g=p.parent/'gameplay'
f=g/'banshee-demo-blitter-service-interpreter020-paula-6000-blitter-locked';ref=g/'banshee-demo-pixel4-interpreter020-paula-6000-denise-locked'
s=(f/'run.log').read_text();r=(ref/'run.log').read_text();pat=r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
assert re.search(pat,s).groups()==re.search(pat,r).groups()
assert json.loads((f/'metrics.json').read_text())['pixels_sha256']==json.loads((ref/'metrics.json').read_text())['pixels_sha256']
assert not re.search(r'^STAGE ',s,re.M)
assert 'PASS positive control' in (p/'positive-control.log').read_text()
for marker in ('UAE_MACHINE PASS','failed=0','witness_bad=0','register_mismatches=00000000','owned memory released','error=0 stopped=1'):assert marker in s
print('PASS profile output matches reference; no nonzero stages; forced-call control records samples')
