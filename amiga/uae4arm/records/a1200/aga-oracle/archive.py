from pathlib import Path
import hashlib,json,shutil
p=Path('.context/amiga/uae4arm/a1200/aga-oracle')
d=Path('amiga/uae4arm/records/a1200/aga-oracle');d.mkdir(parents=True,exist_ok=True)
assert len(json.loads((p/'results.json').read_text()))==9
assert len(json.loads((p/'hardware-results.json').read_text()))==8
assert 'temporary ROM removed; Core1 free' in (p/'hardware.log').read_text()
for f in p.rglob('*'):
 if f.is_file() and f.suffix in ('.md','.py','.json','.log','.txt','.png') and f.name!='REPORT.md':
  target=d/f.relative_to(p);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
inputs={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.glob('*.rom')}
elf=p.parent/'gameplay/build-pixel4/uae-machine.elf'
inputs['uae-machine.elf']=hashlib.sha256(elf.read_bytes()).hexdigest()
for name in ('aga_fetch_fixture.py','check_aga_fetch.py','check_machine.py'):
 f=Path('tests/amiga/uae4arm')/name
 inputs['tests/amiga/uae4arm/'+name]=hashlib.sha256(f.read_bytes()).hexdigest()
(d/'input-sha256.json').write_text(json.dumps(inputs,indent=2)+'\n')
shutil.copy2(p/'REPORT.md',d.parent/'AGA-FETCH-ORACLE.md')
manifest={str(f.relative_to(d)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(d.rglob('*')) if f.is_file() and f.name!='SHA256.json'}
(d/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Archived',len(manifest),'evidence files, no game or Kickstart media.')
