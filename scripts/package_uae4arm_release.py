#!/usr/bin/env python3
"""Package the recorded ZZUAE executables, without settings or user media."""
import argparse, hashlib, json, shutil, zipfile
from pathlib import Path
from uae4arm_version import VERSION
ROOT=Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--launcher-dir',type=Path,required=True)
 p.add_argument('--player',type=Path,required=True)
 p.add_argument('--player-manifest',type=Path,required=True)
 p.add_argument('--icon',type=Path,required=True)
 p.add_argument('--picolibc-license',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args(); out=a.output;out.mkdir(parents=True,exist_ok=True)
 lm=json.loads((a.launcher_dir/'build.json').read_text())
 assert lm['version']==VERSION
 files={}
 for name in ['ZZUAE','ZZUAE-MakeIcon','Install-Scanlines','Scanlines/ZZScanlines','Scanlines/ZZScanlinesGUI']:
  data=(a.launcher_dir/name).read_bytes();assert data[:4]==bytes.fromhex('000003f3')
  expected=lm['sha256'] if name=='ZZUAE' else lm['icon_sha256'] if name=='ZZUAE-MakeIcon' else lm['scanlines'][Path(name).name]
  assert sha(data)==expected,name
  files[name]=data
 files['ZZUAE-Player']=a.player.read_bytes()
 pm=json.loads(a.player_manifest.read_text())
 # Validate against the original player manifest, without rebuilding the tested core.
 assert sha(files['ZZUAE-Player']) in json.dumps(pm),'Player absent from build manifest'
 files['ZZUAE.info']=a.icon.read_bytes()
 assert files['ZZUAE.info'][:2]==bytes.fromhex('e310') and files['ZZUAE.info'][48]==3
 for f in (ROOT/'amiga/uae4arm/scanlines/vendor').iterdir():
  if f.is_file():files['Scanlines/Source/vendor/'+f.name]=f.read_bytes()
 files['Scanlines/ReadMe.md']=(ROOT/'amiga/uae4arm/scanlines/README.md').read_bytes()
 files['ReadMe.txt']=(ROOT/'amiga/uae4arm/installer/ReadMe.txt').read_bytes()
 files['Licenses/GPL-3.0.txt']=(ROOT/'amiga/uae4arm/scanlines/vendor/LICENSE').read_bytes()
 files['Licenses/picolibc.txt']=a.picolibc_license.read_bytes()
 files['SHA256SUMS']=''.join(sha(v)+'  '+k+'\n' for k,v in sorted(files.items())).encode()
 archive=out/f'ZZUAE-{VERSION}.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED)as z:
  for name,data in sorted(files.items()):z.writestr('ZZUAE/'+name,data)
 record={'version':VERSION,'executables':{n:{'bytes':len(d),'sha256':sha(d)}for n,d in files.items()if d[:4]==bytes.fromhex('000003f3')}}
 manifest=ROOT/'.context/amiga/uae4arm/release-build.json';manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_text(json.dumps(record,indent=2)+'\n')
 print(archive)
if __name__=='__main__':main()
