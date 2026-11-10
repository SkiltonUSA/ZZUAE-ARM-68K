from pathlib import Path
import json, re

p = Path('.context/amiga/uae4arm/a1200/blitter-service')
g = p.parent / 'gameplay'
rows = []
for variant in ('pixel4', 'blitter-flag-fast'):
    suffix='reference' if variant=='pixel4' else 'candidate'
    folder = g / f'banshee-demo-{variant}-interpreter020-paula-6000-blitter-fast-{suffix}'
    log = (folder / 'run.log').read_text()
    data = json.loads((folder / 'metrics.json').read_text())
    data['variant'] = variant
    for marker in ('UAE_MACHINE PASS', 'failed=0', 'witness_bad=0',
                   'register_mismatches=00000000', 'owned memory released',
                   'error=0 stopped=1', 'input_events=0'):
        assert marker in log, marker
    data['state'] = re.search(r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)', log).groups()
    data['pcm'] = re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)', log).groups()
    assert data['pcm'][0] == data['pcm'][1] == data['pcm'][2] == '3330048'
    if rows:
        assert data['state'] == rows[0]['state']
        assert data['pixels_sha256'] == rows[0]['pixels_sha256']
    data['change_percent'] = 100 * (data['mean_emulated_fps'] / (rows[0]['mean_emulated_fps'] if rows else data['mean_emulated_fps']) - 1)
    rows.append(data)
(p / 'results.json').write_text(json.dumps(rows, indent=2) + '\n')
for row in rows:
    print(row['variant'], row['mean_emulated_fps'], row['change_percent'], 'gaps', row['pcm'][3])
print('PASS matched guest state/pixels, PCM delivery and cleanup')
