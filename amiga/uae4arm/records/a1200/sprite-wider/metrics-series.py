from pathlib import Path
import sys,asyncio,runpy,subprocess,hashlib,json,re,os
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
from bridge import connect,upload
P=Path('.context/amiga/uae4arm/a1200/performance');APP='SD032G:Emulator/ZZUAE/A1200-Test'
fetch=runpy.run_path('amiga/records/2026-10-07/inventory/fetch.py')['fetch']
games={'alfred-nosetpatch':('Disks/AlfredNoSetPatch.adf','AlfredChicken-2.adf'),'1869hdf':('Disks/1869-hdf.adf',''),'1869':('Disks/1869-auto.adf','1869AGA-B.adf'),'banshee-demo':('Disks/BansheeDemo.adf',''),'banshee':('Disks/Banshee-1.adf','Disks/Banshee-2.adf'),'arcade-pool':('Disks/ArcadePool.adf',''),'slamdemo':('slamdemo.adf',''),'alien':('AlienBreed3D-1.adf','AlienBreed3D-2.adf'),'alfred':('AlfredChicken-1.adf','AlfredChicken-2.adf')}
async def action(call,shell):
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 if '--upload-extra' in sys.argv:
  files=[(P/('build-'+v+'/machine/ZZUAEBoot'),APP+'/ZZUAETest'+v) for v in ['slamscalar','slamfast']]
  files+=[(P/'Alfred-no-setpatch.adf',APP+'/Disks/AlfredNoSetPatch.adf')]
  await upload(call,shell,files)
  for _,dest in files[:2]:await shell(f'Protect "{dest}" +e')
  return
 if '--upload-chipreads' in sys.argv:
  await upload(call,shell,[(P/'build-chipreads/machine/ZZUAEBoot',APP+'/ZZUAETestchipreads')])
  await shell(f'Protect "{APP}/ZZUAETestchipreads" +e')
  return
 if '--upload-candidates' in sys.argv:
  files=[(P/('build-'+v+'/machine/ZZUAEBoot'),APP+'/ZZUAETest'+v) for v in ['neon320','profile','o3']]
  files += [(P/'1869-all.hdf',APP+'/1869-all.hdf'),(P/'1869-hdf.adf',APP+'/Disks/1869-hdf.adf')]
  await upload(call,shell,files)
  for _,dest in files[:3]:await shell(f'Protect "{dest}" +e')
  return
 if '--upload' in sys.argv:
  await upload(call,shell,[(P/'build-scalar/machine/ZZUAEBoot',APP+'/ZZUAETestScalar'),(P/'build-neon/machine/ZZUAEBoot',APP+'/ZZUAETestNeon'),(P/'1869-auto.adf',APP+'/Disks/1869-auto.adf')])
  await shell(f'Protect "{APP}/ZZUAETestScalar" +e\nProtect "{APP}/ZZUAETestNeon" +e')
  return
 names=sys.argv[1].split(',');variant=sys.argv[2];engine=sys.argv[3] if len(sys.argv)>3 else 'INTERPRETER020';audio=sys.argv[4] if len(sys.argv)>4 else 'OFF';frames=int(sys.argv[5]) if len(sys.argv)>5 else 6000
 if engine=='JIT' and len(sys.argv)<=5:frames=3000
 for name in names:
  label=f'{name}-{variant}-{engine.lower()}-{audio.lower()}-{frames}';label+=os.environ.get('ZZ_TEST_TAG','');folder=P/label;folder.mkdir(exist_ok=True)
  assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
  d0,d1=games[name]
  exe={'neon':'ZZUAETestNeon','scalar':'ZZUAETestScalar'}.get(variant,'ZZUAETest'+variant)
  cmd=f'"{APP}/{exe}" a1200a01 RUN "{APP}/{d0}" {frames} ROM "{APP}/Kick31.rom" MODEL A1200 ENGINE {engine} VIDEO PAL FPS 50 LIVE FULLSCREEN AUDIO {audio} WRITE LMB'
  if name=='1869hdf':cmd+=f' HDF "{APP}/1869-all.hdf"'
  if d1:cmd+=f' DF1 "{APP}/{d1}"'
  (folder/'command.txt').write_text(cmd+'\n')
  print('START',label,flush=True)
  print(await shell('Stack 262144\nRun >NIL: '+cmd+' >RAM:A1200.log'),flush=True)
  for i in range(110):
   await asyncio.sleep(3)
   if 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{}):break
  else:raise RuntimeError('worker remains active; stop series')
  log=await shell('Type RAM:A1200.log');(folder/'run.log').write_text(log)
  assert 'owned memory released' in log and 'witness_bad=0' in log and 'register_mismatches=00000000' in log,log
  assert 'UAE_MACHINE PASS' in log and 'failed=0' in log,log
  result=re.search(r'UAE_MACHINE.* frames=(\d+)',log);assert result and int(result[1])==frames,log
  fetch('RAM:ZZUAE-Boot.rgb565',folder/'final.rgb565',327680)
  subprocess.run(['python3',str(P.parent/'pixels.py'),str(folder/'final.rgb565'),str(folder/'final.png')],check=True,stdout=subprocess.DEVNULL)
  progress=[tuple(map(int,m)) for m in re.findall(r'PROGRESS frames=(\d+) elapsed_us=(\d+)',log)]
  last=[(b[0]-a[0])*1e6/(b[1]-a[1]) for a,b in zip(progress,progress[1:]) if a[0]>=3000]
  elapsed=int(re.search(r'BOOT elapsed_us=(\d+)',log)[1]);metrics={'frames':frames,'elapsed_us':elapsed,'mean_emulated_fps':frames*1e6/elapsed,'last_intervals_displayed_fps':last,'pixels_sha256':hashlib.sha256((folder/'final.rgb565').read_bytes()).hexdigest()}
  (folder/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
  print('DONE',label,metrics,flush=True)
asyncio.run(connect(action))
