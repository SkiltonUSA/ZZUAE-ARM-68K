from pathlib import Path
import sys,asyncio,runpy
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
from bridge import connect,upload
p=Path('.context/amiga/uae4arm/a1200/gameplay');app='SD032G:Emulator/ZZUAE/A1200-Test'
variant=sys.argv[1]
async def action(call,shell):
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 source=p/('build-'+variant)/'machine/ZZUAEBoot'
 await upload(call,shell,[(source,app+'/ZZUAETest'+variant)])
 await shell(f'Protect "{app}/ZZUAETest{variant}" +e')
asyncio.run(connect(action))
f=Path('.context/amiga/uae4arm/a1200/performance/series.py')
s=f.read_text().replace("P=Path('.context/amiga/uae4arm/a1200/performance')", "P=Path('.context/amiga/uae4arm/a1200/gameplay')")
s=s.replace("log=await shell('Type RAM:A1200.log')", "log=fetch('RAM:A1200.log',folder/'run.log').decode('latin1')")
sys.argv=[str(f),'banshee-demo',variant,'INTERPRETER020',sys.argv[2] if len(sys.argv)>2 else 'PAULA',sys.argv[3] if len(sys.argv)>3 else '6000']
exec(compile(s,str(f),'exec'))
