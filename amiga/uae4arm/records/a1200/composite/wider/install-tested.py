from pathlib import Path
import sys,asyncio,re,json,hashlib,runpy
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
from bridge import connect,upload
P=Path('.context/amiga/uae4arm/a1200/composite');APP='SD032G:Emulator/ZZUAE/A1200-Test'
base=P.parent/'build/jit-execution-32768-instruction-timing-movw-events-armv7-flatcycles-earlydraw-pressure-registers-batch-neonplanes-neonhalf-chipreads-pixel4'
fpu=P/'pixel-fpu/fpu-execution'
fetch=runpy.run_path('amiga/records/2026-10-07/inventory/fetch.py')['fetch']
async def action(call,shell):
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 records=[json.loads((folder/'build-manifest.json').read_text()) for folder in [base,fpu]]
 assert records[0]['version']==records[1]['version']=='0.6.0-dev'
 assert all(r['upstream']['aga_pixel_loop'] and r['upstream']['chip_reads'] for r in records)
 assert (base/'drawing.o').read_bytes()==(fpu/'drawing.o').read_bytes()
 await upload(call,shell,[(base/'machine/ZZUAEBoot',APP+'/ZZUAETestProduct'),(fpu/'machine/ZZUAEOCS',APP+'/ZZUAETestFPUCheck')])
 await shell(f'Protect "{APP}/ZZUAETestProduct" +e\nProtect "{APP}/ZZUAETestFPUCheck" +e')
 for mode in ('PAL','NTSC'):
  for display in ('WINDOW','FULLSCREEN'):
   name='pixel-product-'+mode.lower()+'-'+display.lower();rom='aga-test.rom' if mode=='PAL' else 'aga-ntsc.rom'
   assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
   cmd=f'"{APP}/ZZUAETestProduct" a1200a01 RUN "" 120 ROM "{APP}/{rom}" MODEL A1200 ENGINE INTERPRETER020 VIDEO {mode} FPS MAX LIVE AUDIO OFF'+(' FULLSCREEN' if display=='FULLSCREEN' else '')
   await shell('Stack 262144\nRun >NIL: '+cmd+' >RAM:A1200.log')
   for i in range(45):
    await asyncio.sleep(2)
    if 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{}):break
   else:raise RuntimeError('worker active')
   log=fetch('RAM:A1200.log',P/(name+'.log')).decode('latin1')
   assert all(s in log for s in ('owned memory released','witness_bad=0','register_mismatches=00000000','failed=0','simd_errors=0','UAE_MACHINE PASS')),log
   assert re.search(r'BITPLANES neon_rows=[1-9]',log) and re.search(r'PIXELS neon_rows=[1-9]',log),log
   assert re.search(r'UAE_MACHINE dispatches=.* frames=120 ',log),log
   print('PASS',name,flush=True)
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 await shell(f'Stack 262144\nRun >NIL: "{APP}/ZZUAETestFPUCheck" a1200a01 RUN >RAM:A1200.log')
 for i in range(45):
  await asyncio.sleep(2)
  if 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{}):break
 else:raise RuntimeError('FPU worker active')
 log=fetch('RAM:A1200.log',P/'pixel-product-fpu-hardware.log').decode('latin1')
 assert all(s in log for s in ('owned memory released','witness_bad=0','register_mismatches=00000000','GUEST_FPU VERIFY PASS')),log
 print('PASS product FPU hardware',flush=True)
 # All original binaries remain available locally for rollback.
 oldbase=base.with_name(base.name.removesuffix('-pixel4'))/'machine/ZZUAEBoot'
 oldfpu=P.parent/'performance/chip-fpu/fpu-execution/machine/ZZUAEBoot'
 for name,local in [('ZZUAE-JIT',oldbase),('ZZUAE-A1200',oldbase),('ZZUAE-FPU',oldfpu)]:
  assert hashlib.md5(local.read_bytes()).hexdigest() in await shell(f'C:MD5Sum "{APP}/{name}"')
 # Promote only to the already-experimental A1200 drawer, after all checks.
 files=[(base/'machine/ZZUAEBoot',APP+'/ZZUAE-JIT'),(base/'machine/ZZUAEBoot',APP+'/ZZUAE-A1200'),(fpu/'machine/ZZUAEBoot',APP+'/ZZUAE-FPU')]
 await upload(call,shell,files)
 for _,dest in files:await shell(f'Protect "{dest}" +e')
 (P/'installed-pixel-builds.json').write_text(json.dumps([{'path':dest,'bytes':local.stat().st_size,'sha256':hashlib.sha256(local.read_bytes()).hexdigest()} for local,dest in files],indent=2)+'\n')
 print('INSTALLED experimental A1200 players',flush=True)
asyncio.run(connect(action))
