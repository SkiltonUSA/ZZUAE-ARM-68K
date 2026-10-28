"""Synthetic 68000 programs for Copper/CPU ordering; no external ROM required."""
import struct


def program(fixture, audio=False):
    code = bytearray.fromhex('13fc000200bfe001')  # Remove ROM overlay.

    def word(value, address):
        code.extend(struct.pack('>HHI', 0x33fc, value, address))

    if audio:
        for i in range(16):
            word(0x4040 if i < 8 else 0xc0c0, 0x2000 + i * 2)
        for channel in range(2):
            for offset, value in [(0, 0), (2, 0x2000), (4, 16),
                                  (6, 200 + channel * 200), (8, 64)]:
                word(value, 0xdff0a0 + channel * 16 + offset)

    copper = []
    for y in range(48, 225, 16):
        copper.extend([y * 256 + 1, 0xfffe])
        for x in range(0x30, 0xd0, 16):
            copper.extend([y * 256 + x + 1, 0xfffe,
                           0x180, (x * 23 + y * 13) & 0xfff])
            if fixture == 'skip':
                # One taken SKIP and one untaken SKIP before colour MOVEs.
                copper.extend([0x0001, 0xffff, 0x180, 0xf00,
                               0xf001, 0xffff, 0x180, 0x0f0])
        if fixture == 'lineend':
            # A horizontal target past the PAL line end must resume next line;
            # prediction must preserve the final odd Copper cycle.
            copper.extend([y * 256 + 0xff, 0xfffe, 0x180, 0x0ff])
    copper.extend([0xffff, 0xfffe])
    for i, value in enumerate(copper):
        word(value, 0x3000 + i * 2)
    for value, address in [(0x2c81, 0xdff08e), (0x2cc1, 0xdff090),
                           (0x38, 0xdff092), (0xd0, 0xdff094),
                           (0, 0xdff0e0), (0x5000, 0xdff0e2),
                           (0x1000, 0xdff100), (0, 0xdff080),
                           (0x3000, 0xdff082),
                           (0x8383 if audio else 0x8380, 0xdff096),
                           (0, 0xdff088)]:
        word(value, address)

    if fixture in ('cpuwrites', 'colorwrite', 'listtoggle', 'restart'):
        loop = len(code)
        code.extend(bytes.fromhex('4e71') * 64)
        if fixture in ('cpuwrites', 'listtoggle'):
            word(0x0fff, 0x3006)  # Change the first horizontal WAIT's mask.
        if fixture == 'listtoggle':
            code.extend(bytes.fromhex('4e71') * 64)
            word(0xfffe, 0x3006)
        if fixture in ('cpuwrites', 'colorwrite'):
            word(0x000f, 0xdff180)
        if fixture in ('cpuwrites', 'restart'):
            word(0, 0xdff088)
        code.extend(struct.pack('>Hh', 0x6000, loop - len(code) - 2))
    else:
        code.extend(bytes.fromhex('60fe'))
    return bytes(code)
