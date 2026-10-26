#!/usr/bin/env python3
"""Package a complete offline AmiPkg installer from a verified emulator ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zipfile
from package_uae4arm_payload import package
from uae4arm_mklha import entry
ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip', type=Path)
    p.add_argument('--key', type=Path, required=True, help='External private signing key; never included')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    m = json.loads((ROOT/'.context/amiga/uae4arm/release-build.json').read_text())
    app = 'ZZUAE'
    version = m['version']; ident = app.lower(); out = a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    build = ROOT/'.context/amiga/uae4arm/installer'; source = build/'client-src'
    # Validate the entire payload before creating the installer.
    with zipfile.ZipFile(a.zip) as z:
        for n, record in m['executables'].items():
            data = z.read(app+'/'+n)
            if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
                raise ValueError('Untested executable: '+n)
        icon = z.read(app+'/'+app+'.info')
    archive, manifest = package(a.zip, out/'repository', app, version,
                               'https://zzemu.invalid/offline/'+app+'-'+version+'.lha')
    manifest['recipe']['ops'] = [
        dict(op='preScript',lines=['FailAt 5','Stack 65536','ZZPKG:ZZUAEInstall check '+app]),
        dict(op='copyTree',src=app,dest='ZZEMUDEST:'),
        dict(op='postScript',lines=['FailAt 5','Stack 32768','ZZEMUDEST:Install-Scanlines'])]
    manifest['requiredCapabilities']=['copy-tree-v1','pre-post-script-v1']
    manifest['requirements']['minKS']='3.1'
    directory = out/(app+'-Install')
    if directory.exists():shutil.rmtree(directory)
    for name in ['Tools','Repository','Licenses']:(directory/name).mkdir(parents=True,exist_ok=True)
    shutil.copy2(source/'amipkg',directory/'Tools/amipkg')
    shutil.copy2(build/'ZZUAEInstall',directory/'Tools/ZZUAEInstall')
    for name in ['LICENSE','NOTICE']:shutil.copy2(source/name,directory/('Licenses/amipkg-'+name))
    shutil.copy2(ROOT/'scripts/amipkg-zzinstall.patch',directory/'Licenses/amipkg-zzinstall.patch')
    shutil.copy2(ROOT/'amiga/uae4arm/installer/main.c',directory/'Licenses/ZZUAEInstall-source.c')
    shutil.copy2(ROOT/'docs/amiga-uae4arm-installer.md',directory/'Installer-guide.md')
    # Include the helper's GPL licence explicitly alongside the client Apache licence.
    shutil.copy2(ROOT/'amiga/uae4arm/scanlines/vendor/LICENSE',directory/'Licenses/ZZUAEInstall-GPL')
    signer = source/'tools/amipkg-repo-sign'
    public = subprocess.check_output([sys.executable,str(signer),'pubkey',str(a.key)],text=True).strip()
    catalog=directory/'Repository/packages.json'
    catalog.write_text(json.dumps(dict(schema=1,indexVersion=1,packages=[manifest]),indent=2)+'\n')
    subprocess.run([sys.executable,str(signer),'sign',str(a.key),str(catalog)],check=True)
    subprocess.run([sys.executable,str(signer),'verify',public,str(catalog)],check=True)
    (directory/'Repository/public.key').write_text(public+'\n')
    shutil.copy2(archive,directory/'Repository'/archive.name)
    # The catalogue carries the complete recipe; no external feed is required.
    (directory/'Install').write_text(f'''.key DEST/K
.bra {{
.ket }}
.def DEST ""
FailAt 5
Stack 65536
If NOT EXISTS C:lha
  Echo "Missing C:lha. Install LhA and retry."
  Quit 10
EndIf
Tools/ZZUAEInstall check {app}
Tools/ZZUAEInstall verify Repository/packages.json Repository/packages.json.sig Repository/public.key
If "{{DEST}}" EQ ""
  Set target `Tools/ZZUAEInstall choose {app}`
Else
  Set target "{{DEST}}"
EndIf
If "$target" EQ ""
  Echo "No destination selected."
  Quit 10
EndIf
If NOT EXISTS "$target"
  MakeDir "$target"
EndIf
If NOT EXISTS "$target/PackageManager"
  MakeDir "$target/PackageManager"
EndIf
If NOT EXISTS "$target/PackageManager/db"
  MakeDir "$target/PackageManager/db"
EndIf
Copy Tools/amipkg "$target/PackageManager/amipkg"
Copy Tools/ZZUAEInstall "$target/PackageManager/ZZUAEInstall"
Protect "$target/PackageManager/amipkg" +e
Protect "$target/PackageManager/ZZUAEInstall" +e
Assign ZZPKG: "$target/PackageManager"
Assign ZZEMUDEST: "$target"
FailAt 21
ZZPKG:amipkg repo remove zzdist >NIL:
FailAt 5
ZZPKG:amipkg repo add zzdist https://zzemu.invalid/offline {public}
ZZPKG:amipkg repo disable official
If NOT EXISTS ZZPKG:repos
  MakeDir ZZPKG:repos
EndIf
If NOT EXISTS ZZPKG:repos/zzdist
  MakeDir ZZPKG:repos/zzdist
EndIf
Copy Repository/packages.json ZZPKG:repos/zzdist/packages.json
Copy Repository/packages.json.sig ZZPKG:repos/zzdist/packages.json.sig
Copy Repository/#?.lha ZZPKG:cache/
ZZPKG:amipkg install zzdist:{ident}
ZZEMUDEST:Install-Scanlines
If NOT EXISTS "$target.info"
  Copy Drawer.info "$target.info"
EndIf
If NOT EXISTS ZZEMUDEST:ROMs
  MakeDir ZZEMUDEST:ROMs
EndIf
If NOT EXISTS ZZEMUDEST:Disks
  MakeDir ZZEMUDEST:Disks
EndIf
If NOT EXISTS ZZEMUDEST:Screenshots
  MakeDir ZZEMUDEST:Screenshots
EndIf
Echo "Installation complete. Open {app} in the selected drawer."
''')
    drawer = bytearray(icon);drawer[48]=2;drawer[58:66]=struct.pack('>II',0x80000000,0x80000000)
    (directory/'Drawer.info').write_bytes(drawer)
    icon_path=directory/'Tools/app.info';icon_path.write_bytes(icon)
    subprocess.run([sys.executable,str(source/'dist/mkprojicon.py'),str(icon_path),str(directory/'Install.info'),'C:IconX'],check=True)
    icon_path.unlink()
    (directory/'ReadMe.txt').write_text((ROOT/'amiga/uae4arm/installer/ReadMe.txt').read_text())
    files={str(f.relative_to(directory.parent)):f.read_bytes() for f in directory.rglob('*') if f.is_file()}
    files[directory.name+'.info']=bytes(drawer)
    installer=out/(app+'-'+version+'-amipkg.lha')
    with installer.open('wb') as stream:
        for name,data in sorted(files.items()):stream.write(entry(name,data))
        stream.write(b'\0')
    receipt=dict(app=app,version=version,client='0.7.11-zzinstall1',payload_sha256=sha(archive),
                 installer_sha256=sha(installer),executables=m['executables'],
                 installer_sources={str(f.relative_to(ROOT)):sha(f) for f in [ROOT/'amiga/uae4arm/installer/main.c',ROOT/'scripts/build_uae4arm_installer.py',ROOT/'scripts/package_uae4arm_installer.py',ROOT/'scripts/amipkg-zzinstall.patch']})
    (out/(app+'-release.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS offline installer:',installer,installer.stat().st_size,'bytes')
if __name__=='__main__':main()
