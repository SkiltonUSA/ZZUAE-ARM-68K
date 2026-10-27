"""Check that a large-cache image cannot silently use the 32 MiB contract."""
import struct
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / 'amiga/uae4arm'))
from elf import unpack

data = Path(sys.argv[1]).read_bytes()
unpack(data, allocation_size=0x4000000)


def rejected(image, allocation=0x2000000):
    try:
        unpack(image, allocation_size=allocation)
    except ValueError:
        return
    raise AssertionError('invalid allocation/image contract accepted')


rejected(data)
rejected(data, 0x8000000)
header = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
for index in range(header[11]):
    at = header[5] + index * header[10]
    section = struct.unpack_from('<10I', data, at)
    if section[1] == 8 and section[2] & 2:
        broken = bytearray(data)
        struct.pack_into('<I', broken, at + 20, 0x4000000 - 0x30000 - 0x640000)
        rejected(broken, 0x4000000)
        break
else:
    raise AssertionError('no BSS section tested')
print('PASS large image requires explicit 64 MiB allocation; stack overlap and unsupported allocation rejected')
