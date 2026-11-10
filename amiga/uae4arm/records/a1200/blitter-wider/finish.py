from pathlib import Path
import sys,asyncio,json,hashlib
sys.path.insert(0,'.context/amiga/c64/trainyard-review')
from bridge import connect
p=Path('.context/amiga/uae4arm/a1200/blitter-wider');app='SD032G:Emulator/ZZUAE/A1200-Test'
async def action(call,shell):
 assert (p.parent/'composite/installed-pixel-builds.json').exists()
 assert 'Sixies.ARM.Debug.Owner' not in await call('amiga_list_ports',{})
 for name in ('blit-table-reference','blit-table-candidate','blitter-flag-fast','pixel4'):
  await shell(f'If EXISTS "{app}/ZZUAETest{name}"\nDelete "{app}/ZZUAETest{name}"\nEndIf')
 base=p.parent/'build/jit-execution-32768-instruction-timing-movw-events-armv7-flatcycles-earlydraw-pressure-registers-batch-neonplanes-neonhalf-chipreads-pixel4/machine/ZZUAEBoot'
 fpu=p.parent/'composite/pixel-fpu/fpu-execution/machine/ZZUAEBoot'
 verified=[]
 for name,local in [('ZZUAE-JIT',base),('ZZUAE-A1200',base),('ZZUAE-FPU',fpu)]:
  expected=hashlib.md5(local.read_bytes()).hexdigest()
  output=await shell(f'C:MD5Sum "{app}/{name}"')
  assert expected in output,(name,output)
  verified.append({'name':name,'md5':expected})
 (p/'verified-installed-players.json').write_text(json.dumps(verified,indent=2)+'\n')
 ports=await call('amiga_list_ports',{})
 assert 'Sixies.ARM.Debug.Owner' not in ports
 (p/'final-ports.log').write_text(ports)
 print('PASS private profiling test executables removed; Core1 free; installed players remain unchanged.')
asyncio.run(connect(action))
