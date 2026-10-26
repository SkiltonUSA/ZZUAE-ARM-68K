#!/usr/bin/env python3
"""Decode a diagnostic little-endian RGB565 capture without resampling."""
import argparse
import struct
import zlib
from pathlib import Path


def png(data, width, height):
    if len(data) != width * height * 2:
        raise ValueError('Capture size does not match dimensions')
    words = struct.unpack('<%dH' % (width * height), data)
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for v in words[y * width:(y + 1) * width]:
            rows.extend(((v >> 11) * 255 // 31,
                         ((v >> 5) & 63) * 255 // 63,
                         (v & 31) * 255 // 31))

    def chunk(kind, payload):
        return (struct.pack('>I', len(payload)) + kind + payload +
                struct.pack('>I', zlib.crc32(kind + payload)))

    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>2I5B', width, height, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, choices=[320, 640], default=640)
    args = parser.parse_args()
    args.output.write_bytes(png(args.capture.read_bytes(), args.width, 256))
