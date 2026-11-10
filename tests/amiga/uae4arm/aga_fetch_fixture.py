"""Original eight-plane diagnostic inspired by NanoMig's aga_test.s method.

No Kickstart or game code. Pixel expectations are calculated independently of
UAE. Rows change colour indices to expose wrong fetch modulo/plane pointers.
"""
import struct
from pathlib import Path

WIDTH = 320
HEIGHT = 192
PLANE = 0x10000
STRIDE = 40
COPPER = 0x8000
DATA = 0x2000


def colour(index):
    return ((index >> 5) * 2 << 8) | (((index >> 2) & 7) * 2 << 4) | ((index & 3) * 4)


def expected_row(y, pattern="stripes"):
    result = []
    for x in range(WIDTH):
        c = colour(((x if pattern == "bits" else x // 8) + y * 13) & 255)
        r, g, b = (c >> 8) * 17, ((c >> 4) & 15) * 17, (c & 15) * 17
        result.extend([((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)] * 2)
    return result


def make_rom(mode, *, ntsc=False, bad_modulo=False, pattern="stripes"):
    assert pattern in ("stripes", "bits", "copper")
    assert mode in range(4)
    rom = bytearray(524288)
    struct.pack_into('>II', rom, 0, 0x7000, 0xf80040)
    struct.pack_into('>HH', rom, 12, 40, 68)
    code = bytearray.fromhex('13fc000200bfe001')  # CIA-A ROM overlay off

    def word(value, address):
        code.extend(struct.pack('>HHI', 0x33fc, value & 65535, address))

    word(0x7fff, 0xdff096)
    word(0x7fff, 0xdff09a)
    word(0x7fff, 0xdff09c)
    # LEA ROM data,A0; LEA Chip RAM,A1; MOVE.W #longwords-1,D0;
    # MOVE.L (A0)+,(A1)+; DBRA D0,copy.
    code.extend(struct.pack('>HIHIHH', 0x41f9, 0xf80000 + DATA,
                            0x43f9, PLANE, 0x303c, STRIDE * HEIGHT * 8 // 4 - 1))
    code.extend(bytes.fromhex('22d851c8fffc'))
    for bank in range(8):
        word(bank << 13, 0xdff106)
        for entry in range(32):
            word(colour(bank * 32 + entry), 0xdff180 + entry * 2)
    word(0, 0xdff106)
    # DDF $38..$d0 consumes 40/44/44/48 bytes: a wide fetch completes
    # its full final sequence beyond DDFSTOP. Keep the stored row at 40 bytes.
    modulo = (0, -4, -4, -8)[mode]
    if bad_modulo:
        modulo += 2
    copper = [0x1fc, mode, 0x100, 0x0210, 0x102, 0, 0x104, 0,
              0x108, modulo & 65535, 0x10a, modulo & 65535,
              0x092, 0x38, 0x094, 0xd0, 0x08e, 0x2c81, 0x090, 0xecc1,
              0x1e4, 0x2000]  # DIWHIGH: HSTOP bit 8, VSTOP=236 (192 rows)
    for plane in range(8):
        address = PLANE + plane * STRIDE * HEIGHT
        copper.extend([0xe0 + plane * 4, address >> 16,
                       0xe2 + plane * 4, address & 65535])
    if pattern == "copper":
        copper.extend([0x182, 0xf00])
        for line in range(64, 225, 16):
            copper.extend([line * 256 + 0x71, 0xfffe, 0x182, 0x0f0,
                           line * 256 + 0xb1, 0xfffe, 0x182, 0x00f,
                           (line + 1) * 256 + 1, 0xfffe, 0x182, 0xf00])
    copper.extend([0xffff, 0xfffe])
    for i, value in enumerate(copper):
        word(value, COPPER + i * 2)
    for value, address in [(0x00 if ntsc else 0x20, 0xdff1dc),
                           (0, 0xdff080), (COPPER, 0xdff082),
                           (0x8380, 0xdff096), (0, 0xdff088)]:
        word(value, address)
    code.extend(bytes.fromhex('60fe'))
    assert len(code) + 64 <= DATA
    rom[64:64 + len(code)] = code
    pixels = bytearray()
    for plane in range(8):
        for y in range(HEIGHT):
            for column in range(STRIDE):
                value = 0
                for bit in range(8):
                    index = (column * 8 + bit + y * 13) & 255 if pattern == "bits" else (column + y * 13) & 255
                    if pattern == "copper":
                        index = 1
                    value |= ((index >> plane) & 1) << (7 - bit)
                pixels.append(value)
    rom[DATA:DATA + len(pixels)] = pixels
    checksum = 0
    for value, in struct.iter_unpack('>I', rom):
        checksum += value
        checksum = (checksum & 0xffffffff) + (checksum >> 32)
    struct.pack_into('>I', rom, len(rom) - 4, (~checksum) & 0xffffffff)
    return bytes(rom)


def verify_pixels(raw, pattern="stripes"):
    assert len(raw) == 640 * 256 * 2
    pixels = struct.unpack('<163840H', raw)
    rows = [list(pixels[y * 640:(y + 1) * 640]) for y in range(256)]
    # Locate the complete first row, then require every following pixel at the
    # same origin. Only vertical framing is discovered; no crop or scaling fit.
    starts = [y for y in range(256 - HEIGHT + 1) if rows[y] == expected_row(0, pattern)]
    assert len(starts) == 1, ('first diagnostic row missing or ambiguous', starts)
    start = starts[0]
    for y in range(HEIGHT):
        want = expected_row(y, pattern)
        if rows[start + y] != want:
            x = next(x for x in range(640) if rows[start + y][x] != want[x])
            raise AssertionError(('pixel mismatch', x, y, rows[start + y][x], want[x]))
    return {'rows': HEIGHT, 'pixels_checked': HEIGHT * 640, 'first_output_row': start}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--mode', type=int, choices=range(4), default=3)
    parser.add_argument('--ntsc', action='store_true')
    args = parser.parse_args()
    args.output.write_bytes(make_rom(args.mode, ntsc=args.ntsc))
