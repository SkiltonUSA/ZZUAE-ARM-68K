"""Compare actual ARM workers: reference ELF, candidate ELF, output directory."""
import json
from pathlib import Path
import subprocess
import sys

reference, candidate, output = map(Path, sys.argv[1:4])
output.mkdir(parents=True, exist_ok=True)
test = Path(__file__).with_name('check_machine.py')
cases = [(name, False) for name in
         ('horizontal', 'skip', 'colorwrite', 'restart', 'cpuwrites', 'listtoggle', 'lineend')]
cases.append(('horizontal', True))
for fixture, audio in cases:
    label = fixture + ('-audio' if audio else '')
    states = []
    for kind, elf in [('reference', reference), ('candidate', candidate)]:
        report = output / (label + '-' + kind + '.json')
        command = [sys.executable, str(test), '12', '--elf', str(elf),
                   '--synthetic-rom', '--profile', '1', '--ram1m', '--live',
                   '--neon', '--copper-fixture', fixture,
                   '--state-report', str(report)]
        if audio:
            command += ['--audio', '--audio-pressure', '--display-rate', '50']
        with report.with_suffix('.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        states.append(json.loads(report.read_text()))
    changed = [key for key in states[0] if states[0][key] != states[1][key]]
    assert not changed, (label, changed)
    detail = 'CPU/CCR, RAM, final pixels and PCM' if audio else 'CPU/CCR, RAM and every presented frame'
    print('PASS', label, detail, flush=True)
