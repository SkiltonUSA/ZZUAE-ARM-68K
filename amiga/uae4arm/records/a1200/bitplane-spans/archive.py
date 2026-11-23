from pathlib import Path
import hashlib
import json
import shutil

work = Path('.context/amiga/uae4arm/a1200/bitplane-spans')
gameplay = work.parent / 'gameplay'
destination = Path('amiga/uae4arm/records/a1200/bitplane-spans')
destination.mkdir(parents=True, exist_ok=True)
for source in work.iterdir():
    if source.is_file() and source.suffix in ('.py', '.cpp', '.patch', '.json', '.log', '.md'):
        if source.name != 'mixed-arm-wrapper.py':
            shutil.copy2(source, destination / source.name)
for variant in ('pixel4', 'denise-once', 'fetch-outline', 'fetch-table', 'bitplane-span-profile'):
    tag = 'spans-locked' if variant == 'bitplane-span-profile' else 'denise-locked'
    source = gameplay / f'banshee-demo-{variant}-interpreter020-paula-6000-{tag}'
    target = destination / variant
    target.mkdir(exist_ok=True)
    for name in ('command.txt', 'metrics.json', 'run.log'):
        shutil.copy2(source / name, target / name)
    shutil.copy2(gameplay / ('build-' + variant) / 'compile.json', target / 'compile.json')
    for fixture in ('memory', 'irq', 'beam', 'colorwrite'):
        for label in ('reference', 'candidate'):
            for suffix in ('.json', '.log'):
                result = gameplay / f'{variant}-{fixture}-{label}{suffix}'
                if result.exists():
                    shutil.copy2(result, target / result.name)
profile = gameplay / 'build-bitplane-span-profile/test-source'
for name in ('profile.h', 'profile.cpp'):
    shutil.copy2(profile / name, destination / name)
manifest = {
    str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted(destination.rglob('*'))
    if path.is_file() and path.name != 'SHA256.json'
}
(destination / 'SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Archived {len(manifest)} evidence files; no game or ROM media.')
