from pathlib import Path
import asyncio,sys
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
from bridge import connect
async def action(call,shell):
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 rows=[]
 for f in ('ENV:Sys/ahi.prefs','ENVARC:Sys/ahi.prefs'):
  rows.append(await shell('C:MD5Sum "'+f+'"'))
 p=Path('.context/amiga/uae4arm/a1200/idle-fetch')
 data='\n'.join(rows)
 if sys.argv[1]=='after':assert data==(p/'prefs-before.log').read_text()
 (p/('prefs-'+sys.argv[1]+'.log')).write_text(data)
 print('PASS',sys.argv[1],'AHI preference hashes',data)
asyncio.run(connect(action))
