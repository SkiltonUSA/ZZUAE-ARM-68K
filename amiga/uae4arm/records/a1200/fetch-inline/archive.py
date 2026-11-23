from pathlib import Path
import hashlib, json, shutil

p = Path('.context/amiga/uae4arm/a1200/fetch-inline')
g = p.parent / 'gameplay'
d = Path('amiga/uae4arm/records/a1200/fetch-inline')
d.mkdir(parents=True, exist_ok=True)
for source in p.iterdir():
    if source.is_file() and source.suffix in ('.py', '.cpp', '.patch', '.json', '.log', '.md', '.asm'):
        if not source.name.startswith('mixed-arm-wrapper') and source.name != 'REPORT.md':
            shutil.copy2(source, d / source.name)
for variant in ('pixel4', 'fetch-inline', 'fetch-fused'):
    target = d / variant
    target.mkdir(exist_ok=True)
    folder = g / f'banshee-demo-{variant}-interpreter020-paula-6000-inline-locked'
    for name in ('command.txt', 'metrics.json', 'run.log'):
        shutil.copy2(folder / name, target / name)
    shutil.copy2(g / ('build-' + variant) / 'compile.json', target / 'compile.json')
    for fixture in ('memory', 'irq', 'beam', 'colorwrite'):
        for label in ('reference', 'candidate'):
            for ext in ('.json', '.log'):
                source = g / f'{variant}-{fixture}-{label}{ext}'
                if source.exists():
                    shutil.copy2(source, target / source.name)
shutil.copy2(p.parent / 'bitplane-spans/check-candidate.py', d / 'check-candidate.py')
manifest = {str(f.relative_to(d)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(d.rglob('*')) if f.is_file() and f.name != 'SHA256.json'}
(d / 'SHA256.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Archived {len(manifest)} evidence files; no ROM or game media.')
