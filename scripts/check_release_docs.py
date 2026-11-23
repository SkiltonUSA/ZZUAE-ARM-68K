#!/usr/bin/env python3
"""Check the public release summary against its version/build record."""
import argparse
import hashlib
import json
from pathlib import Path
import re
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--launcher',type=Path);p.add_argument('--installer',type=Path);a=p.parse_args()
record=json.loads((R/'docs/installer-refresh-inputs.json').read_text())
readme=(R/'README.md').read_text();notes=(R/'docs/release-notes.md').read_text()
version=record['application_version'];number=re.match(r'\d+\.\d+\.\d+',version).group()
assert number in readme.split('<!-- current-release -->',1)[0], 'README title needs current version'
assert version in readme and version in notes,'Current app version missing'
assert re.fullmatch(r'\d+\.\d+\.\d+-(dev|beta|alpha)',record['package_version']), 'Nonstandard package version'
assert record['release_tag'] in readme, 'Current download missing'
assert 'docs/release-notes.md' in readme and 'docs/release-process.md' in readme
for name in ['docs/release-notes.md','docs/release-process.md']:
 assert (R/name).is_file()
if (R/'amiga/c64/launcher.c').exists():
 assert 'New disk' in readme and 'docs/c64-save-disks.md' in readme
 for obsolete in ['Read-only media; FastSID','PRG; read-only D64/D71/D81','Live swapping; read-only images.']:
  assert obsolete not in readme, 'Stale C64 write support: '+obsolete
if a.launcher:
 data=a.launcher.read_bytes();assert version.encode() in data,'Binary version mismatch'
 assert hashlib.sha256(data).hexdigest()==record['launcher_sha256'],'Binary is not recorded release build'
if a.installer:
 from refresh_amipkg_release import read_lha,distribution_documents
 outer=read_lha(a.installer.read_bytes())
 catpath=next(n for n in outer if n.endswith('/Repository/packages.json'))
 cat=json.loads(outer[catpath]);payload={}
 documents=distribution_documents(R)
 folder=catpath.rsplit('/Repository/',1)[0]
 for n,b in documents.items():assert outer[folder+'/'+n]==b, 'Stale/missing installer document: '+n
 for pkg in cat['packages']:
  assert pkg['version']==record['package_version']
  archive=outer[catpath.rsplit('/',1)[0]+'/'+pkg['archive']['url'].rsplit('/',1)[1]]
  assert hashlib.sha256(archive).hexdigest()==pkg['archive']['sha256']
  members=read_lha(archive)
  for n,b in documents.items():assert members[n]==b, 'Stale/missing component document: '+n
  payload.update(members)
 member=record['launcher_member'];data=payload[member]
 assert hashlib.sha256(data).hexdigest()==record['launcher_sha256'], 'Installed launcher differs'
 assert version.encode() in data, 'Installed launcher has stale version'
 assert record['release_tag'].encode() in payload[record['readme_member']], 'Installed README is stale'
 assert len(payload)==len({n.lower() for n in payload}), 'Case-insensitive duplicate path'
 assert sum(n.rsplit('/',1)[-1]==member.rsplit('/',1)[-1] for n in payload)==1, 'Duplicate launcher location'
 print('PASS installer entry point:',member)
print('PASS release docs: version, download, feature guide, checklist'+(' and launcher hash' if a.launcher else ''))
