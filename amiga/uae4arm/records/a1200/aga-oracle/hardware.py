from pathlib import Path
import asyncio, hashlib, json, re, runpy, sys
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
sys.path.insert(0,'tests/amiga/uae4arm')
from bridge import connect,upload
from aga_fetch_fixture import verify_pixels
p=Path('.context/amiga/uae4arm/a1200/aga-oracle')
app='SD032G:Emulator/ZZUAE/A1200-Test'
fetch=runpy.run_path('amiga/records/2026-10-07/inventory/fetch.py')['fetch']
async def action(call,shell):
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 for player,md5 in [('ZZUAE-A1200','c09e0d3d7a0c60e245692201eebbd756'),('ZZUAE-FPU','0e995ed3e7f9bbebacc6acc78ccaba07')]:
  assert md5 in await shell(f'C:MD5Sum "{app}/{player}"')
 results=[]
 for standard in ('pal','ntsc'):
  for mode in range(4):
   name=f'fetch{mode}-{standard}';folder=p/('hardware-'+name);folder.mkdir(exist_ok=True)
   # Model must pass before the same diagnostic is sent to the physical player.
   for wait in range(60):
    model=next((r for r in json.loads((p/'results.json').read_text()) if r['case']==name),None)
    if model is not None:break
    await asyncio.sleep(2)
   assert model is not None, ('model result not ready',name)
   assert model['pixels_checked']==122880
   assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
   await upload(call,shell,[(p/(name+'.rom'),'RAM:ZZUAE-AGA-Test.rom')])
   command=f'"{app}/ZZUAE-A1200" a1200a01 RUN "{app}/Disks/BansheeDemo.adf" 120 ROM "RAM:ZZUAE-AGA-Test.rom" MODEL A1200 ENGINE INTERPRETER020 VIDEO {standard.upper()} FPS 50 LIVE FULLSCREEN AUDIO OFF'
   (folder/'command.txt').write_text(command+'\n')
   print('START',name,flush=True)
   await shell('Stack 262144\nRun >NIL: '+command+' >RAM:ZZUAE-AGA-Test.log')
   for attempt in range(40):
    await asyncio.sleep(2)
    if 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{}):break
   else:raise RuntimeError('Core1 not released; stop testing')
   log=fetch('RAM:ZZUAE-AGA-Test.log',folder/'run.log').decode('latin1')
   for marker in ('UAE_MACHINE PASS','failed=0','owned memory released','witness_bad=0','register_mismatches=00000000'):
    assert marker in log,(name,marker,log)
   assert int(re.search(r'UAE_MACHINE.* frames=(\d+)',log)[1])==120
   raw=fetch('RAM:ZZUAE-Boot.rgb565',folder/'final.rgb565',327680)
   checked=verify_pixels(raw)
   assert hashlib.sha256(raw).hexdigest()==model['sha256'],name
   results.append({'case':name,'sha256':model['sha256'],**checked})
   (p/'hardware-results.json').write_text(json.dumps(results,indent=2)+'\n')
   print('PASS',name,checked,'clean release; matches ARM-model capture',flush=True)
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 await shell('Delete RAM:ZZUAE-AGA-Test.rom\nDelete RAM:ZZUAE-AGA-Test.log')
 for player,md5 in [('ZZUAE-A1200','c09e0d3d7a0c60e245692201eebbd756'),('ZZUAE-FPU','0e995ed3e7f9bbebacc6acc78ccaba07')]:
  assert md5 in await shell(f'C:MD5Sum "{app}/{player}"')
 (p/'final-ports.log').write_text(await call('amiga_list_ports',{}))
 print('PASS installed players unchanged; temporary ROM removed; Core1 free',flush=True)
asyncio.run(connect(action))
