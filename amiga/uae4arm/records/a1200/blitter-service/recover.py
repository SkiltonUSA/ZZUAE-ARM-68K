from pathlib import Path
import runpy,hashlib,json,re
p=Path('.context/amiga/uae4arm/a1200/gameplay/banshee-demo-blitter-service-interpreter020-paula-6000-blitter-locked')
fetch=runpy.run_path('amiga/records/2026-10-07/inventory/fetch.py')['fetch']
raw=fetch('RAM:ZZUAE-Boot.rgb565',p/'final.rgb565',327680)
s=(p/'run.log').read_text();e=int(re.search(r'BOOT elapsed_us=(\d+)',s)[1]);(p/'metrics.json').write_text(json.dumps({'frames':6000,'elapsed_us':e,'pixels_sha256':hashlib.sha256(raw).hexdigest()},indent=2)+'\n')
print('Recovered final capture',hashlib.sha256(raw).hexdigest())
