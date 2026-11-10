#!/usr/bin/env python3
"""Check a built ARM player against independent AGA pixel expectations.

Usage: model-python check_aga_fetch.py player.elf output-directory
Run serially: check_machine.py writes its final capture to boot.rgb565.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from aga_fetch_fixture import make_rom, verify_pixels


def main():
    elf, output = map(Path, sys.argv[1:3])
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[3]
    results = []
    cases = [(mode, ntsc, False) for ntsc in (False, True) for mode in range(4)]
    cases.append((3, False, True))  # Deliberately wrong modulo must fail the oracle.
    for mode, ntsc, bad in cases:
        label = f'fetch{mode}-' + ('ntsc' if ntsc else 'pal') + ('-bad-modulo' if bad else '')
        rom = output / (label + '.rom')
        rom.write_bytes(make_rom(mode, ntsc=ntsc, bad_modulo=bad))
        command = [sys.executable, str(Path(__file__).with_name('check_machine.py')),
                   '16', '--elf', str(elf), '--cache32', '--engine', '2',
                   '--profile', '4', '--synthetic-rom', '--rom', str(rom),
                   '--neon', '--live', '--state-report', str(output / (label + '.json'))]
        if ntsc:
            command.append('--ntsc')
        with (output / (label + '.log')).open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        raw = (root / '.context/amiga/uae4arm/boot.rgb565').read_bytes()
        (output / (label + '.rgb565')).write_bytes(raw)
        try:
            checked = verify_pixels(raw)
        except AssertionError as error:
            if not bad:
                raise
            checked = {'negative_control_rejected': str(error)}
        else:
            assert not bad, 'wrong-modulo ROM passed the pixel oracle'
            # Prove that both low-bit and red-channel pixel corruption fail.
            for mask in (1, 0xf800):
                changed = bytearray(raw)
                offset = (checked['first_output_row'] + 20) * 1280 + 100
                word = int.from_bytes(changed[offset:offset + 2], 'little') ^ mask
                changed[offset:offset + 2] = word.to_bytes(2, 'little')
                try:
                    verify_pixels(changed)
                except AssertionError:
                    pass
                else:
                    raise AssertionError('corrupted pixel passed the oracle')
        results.append({'case': label, 'sha256': hashlib.sha256(raw).hexdigest(), **checked})
        (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        print('PASS', label, checked, flush=True)


if __name__ == '__main__':
    main()
