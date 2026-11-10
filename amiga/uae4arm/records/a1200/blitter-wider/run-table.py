from pathlib import Path
import sys,asyncio,os
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
from bridge import connect,upload
p=Path('.context/amiga/uae4arm/a1200/gameplay');app='SD032G:Emulator/ZZUAE/A1200-Test'
async def setup(call,shell):
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 for variant in ['blit-table-reference','blit-table-candidate']:
  await upload(call,shell,[(p/('build-'+variant)/'machine/ZZUAEBoot',app+'/ZZUAETest'+variant)])
  await shell(f'Protect "{app}/ZZUAETest{variant}" +e')
asyncio.run(connect(setup))
f=Path('.context/amiga/uae4arm/a1200/performance/series.py')
s=f.read_text().replace("P=Path('.context/amiga/uae4arm/a1200/performance')", "P=Path('.context/amiga/uae4arm/a1200/gameplay')").replace("log=await shell('Type RAM:A1200.log')", "log=fetch('RAM:A1200.log',folder/'run.log').decode('latin1')")
s=s.replace('range(110)','range(165)')
os.environ['ZZ_TEST_TAG']='-blit-table'
for game,audio in [('slamdemo','PAULA')]:
 for variant in ['blit-table-reference','blit-table-candidate']:
  sys.argv=[str(f),game,variant,'INTERPRETER020',audio,'9000']
  exec(compile(s,str(f),'exec'),{'__name__':'__main__'})
