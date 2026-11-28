"""Guest-written Chip RAM code: warm a site, then patch bytes and words.

No host cache flush or direct host mutation is used after guest execution starts.
"""
import struct

def program():
    code = bytearray.fromhex('13fc000200bfe001')  # ROM overlay off
    code.extend(bytes.fromhex('23fc70014e7500010000'))  # MOVEQ #1,D0; RTS
    for value in (1, 2, 3):
        if value == 2:
            code.extend(bytes.fromhex('13fc000200010001'))  # patch immediate byte
        elif value == 3:
            code.extend(bytes.fromhex('33fc700300010000'))  # patch instruction word
        code.extend(bytes.fromhex('323c03ff'))  # 1024 calls to the same site
        loop = len(code)
        code.extend(bytes.fromhex('4eb900010000'))
        branch = len(code)
        code.extend(struct.pack('>Hh', 0x51c9, loop - branch - 2))
        code.extend(struct.pack('>HI', 0x23c0, 0x2120 + value * 4))
    code.extend(bytes.fromhex('23fc534d43310000212060fe'))
    return bytes(code)

def verify(machine, symbols):
    chip = struct.unpack('<I', machine.mem_read(symbols['chipmem_bank'] + 32, 4))[0]
    values = struct.unpack('>4I', machine.mem_read(chip + 0x2120, 16))
    assert values == (0x534d4331, 1, 2, 3), values
    print('PASS guest self-modifying code: warmed site, byte patch, word patch; no host flush', values)
