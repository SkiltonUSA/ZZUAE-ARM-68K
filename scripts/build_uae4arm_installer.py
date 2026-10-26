#!/usr/bin/env python3
"""Build the offline installer helper and locally patched AmiPkg client."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

root = Path(__file__).resolve().parents[1]
out = root / '.context/amiga/uae4arm/installer'
source = out / 'client-src'
source.mkdir(parents=True, exist_ok=True)
with tarfile.open(root / 'sources/amipkg-66cfb988.tar.gz') as archive:
    archive.extractall(source, filter='data')
subprocess.run(['patch', '-p1', '-i', str(root / 'scripts/amipkg-zzinstall.patch')], cwd=source, check=True)
image = json.loads((root / 'amiga/upstream.json').read_text())['image']
base = ['podman', '--connection', 'nuflix-converter-root', 'run', '--rm',
        '--platform', 'linux/amd64', '-v', f'{root}:/work', '-w', '/work', image]
src = str(source.relative_to(root))
subprocess.run(base + ['make', '-C', src, 'CPU=68020', 'amipkg'], check=True)
subprocess.run(base + ['m68k-amigaos-gcc', '-m68020', '-Os', '-w', '-c',
                      src + '/src/core/tweetnacl.c', '-o', '.context/amiga/uae4arm/installer/tweetnacl.o'], check=True)
subprocess.run(base + ['m68k-amigaos-gcc', '-std=c99', '-noixemul', '-m68020', '-O2',
                      '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                      '-Wno-misleading-indentation', '-I' + src + '/src/core',
                      'amiga/uae4arm/installer/main.c', src + '/src/core/averify.c',
                      '.context/amiga/uae4arm/installer/tweetnacl.o', '-lamiga',
                      '-o', '.context/amiga/uae4arm/installer/ZZUAEInstall'], check=True)
record = {'amipkg_revision': '66cfb9888f7d6b28d1411ff254817ee14ed4e043',
          'client_version': '0.7.11-zzinstall1', 'image': image,
          'sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (source / 'amipkg', out / 'ZZUAEInstall', root / 'scripts/amipkg-zzinstall.patch')}}
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
print(out)
