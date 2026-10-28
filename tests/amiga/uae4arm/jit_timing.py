#!/usr/bin/env python3
"""Compare interpreter/JIT beam reads and branch cycles in actual ARM code.

Requires an isolated --instruction-timing --player build. This is an
instruction-model regression, not evidence of physical cache/MMU behavior.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--elf', type=Path, required=True)
parser.add_argument('--cache32', action='store_true')
parser.add_argument('--fixtures', nargs='+', choices=['beam','branch','irq','pressure','groups'], default=['beam','branch','irq'])
parser.add_argument('--event-blocks', action='store_true')
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
for fixture in args.fixtures:
    states = []
    for engine in (2, 1):
        name = args.output / f'{fixture}-{engine}'
        command = [sys.executable, str(root/'tests/amiga/uae4arm/check_machine.py'),
                   '1', '--synthetic-rom', '--profile', '1', '--ram1m',
                   '--timing-fixture', fixture, '--engine', str(engine),
                   '--elf', str(args.elf), '--state-report', str(name.with_suffix('.json'))]
        if args.event_blocks:
            command.append('--require-event-blocks')
        if args.cache32:
            command.append('--cache32')
        with name.with_suffix('.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        state = json.loads(name.with_suffix('.json').read_text())
        state['result'][0] = 0  # block dispatches are not guest instructions
        states.append(state)
    assert states[0] == states[1], f'{fixture}: interpreter/JIT state differs; see {args.output}'
    print(f'PASS {fixture}: cycles, PC, registers/CCR, Chip RAM and pixels match', flush=True)
