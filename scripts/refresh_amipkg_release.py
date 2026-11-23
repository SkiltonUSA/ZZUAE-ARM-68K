#!/usr/bin/env python3
"""Refresh a signed offline installer using hash-pinned replacement files.

The input receipt supplies the base installer hash, package revision and explicit
payload changes. Existing install recipes and dependency checks are preserved.
Private signing keys are separate arguments and never enter the output archive.
Requires lhafile and the existing amipkg-repo-sign tool.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import urllib.parse

import lhafile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_lha(data):
    files = {}
    with io.BytesIO(data) as stream:
        archive = lhafile.Lhafile(stream)
        for item in archive.infolist():
            name = item.filename.replace('\\', '/')
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or ':' in name:
                raise ValueError('Unsafe archive member: ' + name)
            if item.compress_type == b'-lhd-':
                continue
            if name in files:
                raise ValueError('Duplicate member: ' + name)
            files[name] = archive.read(item.filename)
    return files


def write_lha(files, output, lha):
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        for name, data in files.items():
            parts = PurePosixPath(name)
            if parts.is_absolute() or '..' in parts.parts or any(c in name for c in '\\:\r\n'):
                raise ValueError('Unsafe output member: ' + name)
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            if data[:4] == bytes.fromhex('000003f3') or path.name == 'Install':
                path.chmod(0o755)
        output.unlink(missing_ok=True)
        subprocess.run([str(lha), 'aq', str(output),
                        *sorted({n.split('/')[0] for n in files})],
                       cwd=stage, check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(lha), 'tq', str(output)], check=True,
                   stdout=subprocess.DEVNULL)
    if read_lha(output.read_bytes()) != files:
        raise ValueError('Archive round-trip mismatch: ' + str(output))


def distribution_documents(repo):
    """Offline documents: README is an exact copy, with original licence text."""
    readme = (repo / 'README.md').read_bytes()
    licence_source = repo / 'docs/distribution-licence.txt'
    if not licence_source.is_file():
        licence_source = repo / 'LICENSE'
    licence = licence_source.read_bytes()
    lines = readme.decode('utf-8').splitlines()
    sections = []
    active = False
    for line in lines:
        if line.startswith('## '):
            active = any(word in line.lower() for word in ('credit', 'acknowledg', 'licenc', 'licens'))
        if active:
            sections.append(line)
    if not sections:
        for name in ('NOTICE.md', 'THIRD_PARTY.md'):
            if (repo / name).is_file():
                sections = (repo / name).read_text().splitlines()
                break
    intro = lines[0].lstrip('# ') + '\n\n'
    about = (intro + '\n'.join(sections) +
             '\n\nLicence: see licence.txt. Component licence notices included in the archive also apply.\n').encode('utf-8')
    return {'readme.txt': readme, 'licence.txt': licence, 'about.txt': about}


def refresh(spec, key, signer, lha, output):
    import sys
    documents = distribution_documents(Path(__file__).resolve().parents[1])
    base = Path(spec['base']).read_bytes()
    if sha(base) != spec['base_sha256']:
        raise ValueError('Base installer changed')
    outer = read_lha(base)
    catalogs = [n for n in outer if n.endswith('/Repository/packages.json')]
    if len(catalogs) != 1:
        raise ValueError('Expected one catalogue')
    catalog_name = catalogs[0]
    folder = catalog_name.removesuffix('/Repository/packages.json')
    catalog = json.loads(outer[catalog_name])
    public = outer[folder + '/Repository/public.key'].decode().strip()
    actual_public = subprocess.check_output(
        [sys.executable, str(signer), 'pubkey', str(key)], text=True).strip()
    if public != actual_public:
        raise ValueError('Signing key differs from installer trust root')
    replaced = set()
    records = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        signed = tmp / 'packages.json'
        signed.write_bytes(outer[catalog_name])
        signed.with_suffix('.json.sig').write_bytes(outer[catalog_name + '.sig'])
        subprocess.run([sys.executable, str(signer), 'verify', public, str(signed)],
                       check=True, stdout=subprocess.DEVNULL)
        for package in catalog['packages']:
            ident = package['id']
            archive_name = urllib.parse.urlparse(package['archive']['url']).path.rsplit('/', 1)[-1]
            old_path = folder + '/Repository/' + archive_name
            old_data = outer.pop(old_path)
            if sha(old_data) != package['archive']['sha256']:
                raise ValueError('Base payload checksum mismatch: ' + ident)
            files = read_lha(old_data)
            for doc in documents:
                files.pop(doc, None)
            for name, change in spec['changes'].get(ident, {}).items():
                data = Path(change['source']).read_bytes()
                if sha(data) != change['sha256']:
                    raise ValueError('Replacement checksum mismatch: ' + name)
                if name.endswith(('.secret', '.sav', '.cfg')):
                    raise ValueError('Personal data in replacement: ' + name)
                files[name] = data
                replaced.add((ident, name))
            # Rebuild existing per-drawer file indexes after replacing binaries.
            for name in list(files):
                if PurePosixPath(name).name not in ('SHA256SUMS', 'SHA256SUMS.json'):
                    continue
                prefix = name.rsplit('/', 1)[0] + '/'
                hashes = {n[len(prefix):]: sha(b) for n, b in sorted(files.items())
                          if n.startswith(prefix) and n != name}
                files[name] = ((json.dumps(hashes, indent=2) + '\n').encode()
                               if name.endswith('.json') else
                               ''.join(h + '  ' + n + '\n' for n, h in hashes.items()).encode())
            if len(files) >= 256:
                raise ValueError('AmiPkg receipt capacity exceeded: ' + ident)
            # Root documents are outside the copyTree application payload;
            # they do not consume installed-file receipt slots.
            files.update(documents)
            package['version'] = spec['version']
            for dep in package.get('deps', []):
                dep['min'] = spec['version']
            new_name = ident + '-' + spec['version'] + '.lha'
            # Model-selectable installers copy individual archives through
            # component scripts rather than a wildcard in the top-level script.
            for name in outer:
                if PurePosixPath(name).name == 'Install' or '/Repository/Component-' in name:
                    outer[name] = outer[name].replace(archive_name.encode(), new_name.encode())
            payload = tmp / new_name
            write_lha(files, payload, lha)
            data = payload.read_bytes()
            outer[folder + '/Repository/' + new_name] = data
            package['archive'].update(url=package['archive']['url'].rsplit('/', 1)[0] + '/' + new_name,
                                      sizeBytes=len(data), sha256=sha(data))
            records[ident] = {'files': {n: sha(b) for n, b in sorted(files.items())},
                              'archive_sha256': sha(data)}
        expected = {(p, n) for p, changes in spec['changes'].items() for n in changes}
        if expected != replaced:
            raise ValueError('Unapplied replacements: ' + str(expected - replaced))
        # Installer helpers/scripts live outside the signed component payloads.
        # Their exact hashes are recorded in the release receipt.
        outer_records = {}
        for name, change in spec.get('installer_changes', {}).items():
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or ':' in name:
                raise ValueError('Invalid installer replacement path: ' + name)
            data = Path(change['source']).read_bytes()
            if sha(data) != change['sha256']:
                raise ValueError('Installer replacement checksum mismatch: ' + name)
            outer[folder + '/' + name] = data
            outer_records[name] = sha(data)
        notes = Path(spec['notes']).read_bytes()
        outer[folder + '/Release-notes.md'] = notes
        original_notes = outer.pop(folder + '/ReadMe.txt', None)
        if original_notes and folder + '/Installer-notes.txt' not in outer:
            outer[folder + '/Installer-notes.txt'] = original_notes
        for name, data in documents.items():
            outer[folder + '/' + name] = data
        signed.write_text(json.dumps(catalog, indent=2) + '\n')
        subprocess.run([sys.executable, str(signer), 'sign', str(key), str(signed)],
                       check=True, stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, str(signer), 'verify', public, str(signed)],
                       check=True, stdout=subprocess.DEVNULL)
        outer[catalog_name] = signed.read_bytes()
        outer[catalog_name + '.sig'] = signed.with_suffix('.json.sig').read_bytes()
        for name in outer:
            if name.endswith(('.secret', '.pem')) or '/lease' in name:
                raise ValueError('Private file in installer: ' + name)
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        write_lha(outer, output, lha)
    receipt = {'version': spec['version'], 'base_sha256': sha(base),
               'installer_sha256': sha(output.read_bytes()),
               'packages': records, 'installer_replacements': outer_records, 'validation': 'signatures, payload hashes and full LHA round-trip; no fresh physical install'}
    output.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('PASS', output.name, output.stat().st_size, 'bytes')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('spec', type=Path)
    p.add_argument('--key', required=True, type=Path)
    p.add_argument('--signer', required=True, type=Path)
    p.add_argument('--lha', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    refresh(json.loads(a.spec.read_text()), a.key.resolve(), a.signer.resolve(),
            a.lha.resolve(), a.output)
