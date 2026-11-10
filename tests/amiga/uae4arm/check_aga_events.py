"""Independent fine-pixel and bounded Copper colour-transition checks."""
import json
import struct
import subprocess
import sys
from pathlib import Path
from aga_fetch_fixture import make_rom, verify_pixels


def verify_copper(raw):
    assert len(raw) == 327680
    values = struct.unpack('<163840H', raw)
    rows = [values[y * 640:(y + 1) * 640] for y in range(256)]
    start = next(y for y, row in enumerate(rows) if any(row))
    assert start + 192 <= 256
    count = 0
    for y in range(192):
        event = (y + 44) in range(64, 225, 16)
        # Interior regions only: do not infer an exact Copper MOVE latency.
        zones = [(0, 64, 0xf800), (160, 224, 0x07e0), (288, 320, 0x001f)] if event else [(0, 320, 0xf800)]
        for left, right, colour in zones:
            assert all(v == colour for v in rows[start + y][left * 2:right * 2]), (y, left, right, colour)
            count += (right - left) * 2
    return {'pixels_checked': count, 'first_output_row': start, 'event_rows': 11}


def main():
    elf, out = map(Path, sys.argv[1:3]);out.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[3]
    results = []
    cases = [("bits", mode, ntsc) for ntsc in (False, True) for mode in range(4)]
    cases += [("copper", 3, ntsc) for ntsc in (False, True)]
    for pattern, mode, ntsc in cases:
        label = f'{pattern}{mode}-' + ('ntsc' if ntsc else 'pal')
        rom = out / (label + '.rom');rom.write_bytes(make_rom(mode, ntsc=ntsc, pattern=pattern))
        cmd = [sys.executable, str(Path(__file__).with_name('check_machine.py')), '16',
               '--elf', str(elf), '--cache32', '--engine', '2', '--profile', '4',
               '--synthetic-rom', '--rom', str(rom), '--neon', '--live']
        if ntsc:cmd.append('--ntsc')
        with (out / (label + '.log')).open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
        raw = (root / '.context/amiga/uae4arm/boot.rgb565').read_bytes()
        (out / (label + '.rgb565')).write_bytes(raw)
        checked = verify_copper(raw) if pattern == 'copper' else verify_pixels(raw, 'bits')
        if pattern == 'copper':
            # A missing mid-line write must fail even if the rest of the frame is correct.
            damaged = bytearray(raw)
            at = ((checked['first_output_row'] + 20) * 640 + 320) * 2
            damaged[at:at + 2] = struct.pack('<H', 0xf800)
            try:verify_copper(damaged)
            except AssertionError:pass
            else:raise AssertionError('missing green transition accepted')
        else:
            # Reverse the eight logical pixels represented by one plane byte.
            damaged = bytearray(raw)
            at = ((checked['first_output_row'] + 10) * 640 + 80) * 2
            group = [damaged[at + n * 4:at + n * 4 + 4] for n in range(8)]
            damaged[at:at + 32] = b''.join(reversed(group))
            try:verify_pixels(damaged, 'bits')
            except AssertionError:pass
            else:raise AssertionError('reversed pixel bits accepted')
        results.append({'case': label, **checked})
        (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        print('PASS', label, checked, flush=True)


if __name__ == '__main__':main()
