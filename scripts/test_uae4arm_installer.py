#!/usr/bin/env python3
"""Check release/installer equivalence, integrity, recipe and private-data exclusions."""
import ctypes,hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def test(directory):
 record=json.loads((ROOT/'.context/amiga/uae4arm/release-build.json').read_text());app='ZZUAE';v=record['version']
 installer=directory/f'{app}-{v}-amipkg.lha';manual=directory/f'{app}-{v}.zip'
 source=ROOT/'.context/amiga/uae4arm/installer/client-src';signer=source/'tools/amipkg-repo-sign'
 with tempfile.TemporaryDirectory() as t:
  t=Path(t);outer=t/'outer';outer.mkdir()
  subprocess.run(['7zz','x','-y','-o'+str(outer),str(installer.resolve())],check=True,stdout=subprocess.DEVNULL)
  d=outer/(app+'-Install');repo=d/'Repository'
  catalog=json.loads((repo/'packages.json').read_text());package=catalog['packages'][0]
  public=(repo/'public.key').read_text().strip()
  subprocess.run([sys.executable,str(signer),'verify',public,str(repo/'packages.json')],check=True,stdout=subprocess.DEVNULL)
  subprocess.run([sys.executable,str(signer),'check',str(repo/'packages.json')],check=True)
  # Exercise the same C signature verifier compiled into the Amiga helper.
  verifier=t/'verify.dylib'
  subprocess.run(['cc','-shared','-fPIC','-w','-O2','-I'+str(source/'src/core'),str(source/'src/core/averify.c'),str(source/'src/core/tweetnacl.c'),'-o',str(verifier)],check=True)
  verify=ctypes.CDLL(str(verifier)).amipkg_verify_index_key
  verify.argtypes=[ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p];verify.restype=ctypes.c_int
  data=(repo/'packages.json').read_bytes();sig=(repo/'packages.json.sig').read_bytes().strip()
  assert verify(data,len(data),sig,public.encode())==1
  changed=bytearray(data);changed[len(changed)//2]^=1
  assert verify(bytes(changed),len(changed),sig,public.encode())==0
  assert verify(data,len(data),sig,b'')==0
  payload=repo/f'{app}-{v}.lha';assert payload.stat().st_size==package['archive']['sizeBytes']
  assert sha(payload.read_bytes())==package['archive']['sha256']
  extracted=t/'payload';extracted.mkdir()
  subprocess.run(['7zz','x','-y','-o'+str(extracted),str(payload)],check=True,stdout=subprocess.DEVNULL)
  with zipfile.ZipFile(manual) as z:
   zipfiles={n:z.read(n)for n in z.namelist()if not n.endswith('/')}
  lhafiles={str(p.relative_to(extracted)):p.read_bytes()for p in extracted.rglob('*')if p.is_file()}
  assert zipfiles==lhafiles,'ZIP/LHA payloads differ'
  for name,r in record['executables'].items():
   data=lhafiles[app+'/'+name];assert len(data)==r['bytes'] and sha(data)==r['sha256']
  for line in lhafiles[app+'/SHA256SUMS'].decode().splitlines():
   digest,name=line.split('  ',1);assert sha(lhafiles[app+'/'+name])==digest
  for p in outer.rglob('*'):
   if not p.is_file():continue
   assert p.suffix.lower()not in {'.secret','.nes','.sfc','.smc','.sav','.zzs','.adf','.rom'},p
   assert p.name.lower()not in {'library.cfg','controls.cfg'},p
  ops=package['recipe']['ops'];assert ops[0]['op']=='preScript' and ops[1]['op']=='copyTree'
  assert ops[1]['dest']=='ZZEMUDEST:' and ops[1]['src']==app
  assert ops[2]['op']=='postScript' and ops[2]['lines'][-1]=='ZZEMUDEST:Install-Scanlines'
  script=(d/'Install').read_text()
  assert script.index('ZZUAEInstall check')<script.index('Copy Tools/amipkg')
  assert script.index('ZZUAEInstall verify')<script.index('Copy Tools/amipkg')
  assert 'Delete 'not in script and 'Startup'not in script
  for name in ['Tools/ZZUAEInstall','Tools/amipkg']:
   assert(d/name).read_bytes()[:4]==bytes.fromhex('000003f3')
  assert(d/'Install.info').read_bytes()[48]==4
  assert(outer/(app+'-Install.info')).read_bytes()[48]==2
  # A changed catalogue must fail authentication before the copy phase.
  changed=repo/'changed.json';changed.write_bytes((repo/'packages.json').read_bytes()+b' ')
  (repo/'changed.json.sig').write_bytes((repo/'packages.json.sig').read_bytes())
  fail=subprocess.run([sys.executable,str(signer),'verify',public,str(changed)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  assert fail.returncode!=0
  print('PASS:',app,'installer/ZIP byte equivalence; recorded executables; all member hashes; dependency-first recipe; corruption rejection; icons; private-data exclusions')
if __name__=='__main__':test(Path(sys.argv[1]))
