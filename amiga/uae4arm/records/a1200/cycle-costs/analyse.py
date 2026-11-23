from pathlib import Path
import json, re

p = Path('.context/amiga/uae4arm/a1200/cycle-costs')
g = p.parent / 'gameplay'
folder = g / 'banshee-demo-fetch-cycle-profile-interpreter020-paula-6000-cycles-locked'
log = (folder / 'run.log').read_text()
reference = g / 'banshee-demo-pixel4-interpreter020-paula-6000-denise-locked'
ref = (reference / 'run.log').read_text()
signature = r'UAE_MACHINE dispatches=(\d+) cycles=(\d+) hash=(\w+) pc=(\w+) frames=(\d+)'
assert re.search(signature, log).groups() == re.search(signature, ref).groups()
assert json.loads((folder / 'metrics.json').read_text())['pixels_sha256'] == json.loads((reference / 'metrics.json').read_text())['pixels_sha256']
for marker in ('UAE_MACHINE PASS', 'failed=0', 'witness_bad=0',
               'register_mismatches=00000000', 'owned memory released',
               'error=0 stopped=1', 'input_events=0'):
    assert marker in log, marker
pcm = re.search(r'AUDIO_TASK queued=(\d+) submitted=(\d+) completed=(\d+).*gaps=(\d+)', log).groups()
assert pcm[0] == pcm[1] == pcm[2] == '3330048'
hz = int(re.search(r'TIMER estimated_hz=(\d+)', log)[1])
names = ('Whole per-cycle function', 'Event prefix', 'Fetch dispatch',
         'Output suffix including flush', 'Nested ChipRAM load/store body', 'Empty timer scope')
rows = []
for stage, hi, lo, count in re.findall(r'^STAGE id=(\d+) ticks_hi=(\d+) ticks_lo=(\d+) calls=(\d+)', log, re.M):
    ticks = (int(hi) << 32) | int(lo)
    rows.append(dict(stage=int(stage), name=names[int(stage)], samples=int(count),
                     estimated_seconds=ticks * 64 / hz,
                     average_ticks=ticks / int(count) if int(count) else 0))
assert len(rows) == 6
(p / 'stages.json').write_text(json.dumps(rows, indent=2) + '\n')
for row in rows:
    print(row)
print('PASS matched guest state/pixels, PCM delivery and clean teardown; gaps', pcm[3])
