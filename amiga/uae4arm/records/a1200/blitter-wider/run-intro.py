from pathlib import Path
import sys,asyncio,os
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
from bridge import connect,upload
p=Path('.context/amiga/uae4arm/a1200/gameplay');app='SD032G:Emulator/ZZUAE/A1200-Test'
async def setup(call,shell):
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 for variant in ['pixel4','blitter-flag-fast']:
  await upload(call,shell,[(p/('build-'+variant)/'machine/ZZUAEBoot',app+'/ZZUAETest'+variant)])
  await shell(f'Protect "{app}/ZZUAETest{variant}" +e')
asyncio.run(connect(setup))
f=Path('.context/amiga/uae4arm/a1200/performance/series.py')
s=f.read_text().replace("P=Path('.context/amiga/uae4arm/a1200/performance')", "P=Path('.context/amiga/uae4arm/a1200/gameplay')").replace("log=await shell('Type RAM:A1200.log')", "log=fetch('RAM:A1200.log',folder/'run.log').decode('latin1')")
os.environ['ZZ_TEST_TAG']='-blitter-wider'
for game,audio in [('slamdemo','PAULA')]:
 for variant in ['pixel4','blitter-flag-fast']:
  sys.argv=[str(f),game,variant,'INTERPRETER020',audio,'6000']
  exec(compile(s,str(f),'exec'),{'__name__':'__main__'})
