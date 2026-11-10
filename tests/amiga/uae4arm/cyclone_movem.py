#!/usr/bin/env python3
"""Run after build_uae4arm_cyclone_probe.py --big-endian --fix-movem.

Exercise the actual generated ARM exception path at different context addresses.
This checks the stacked PC and absence of a data transfer, not full 68000 timing.
"""
import struct
from cyclone_endian import Core

core=Core(True)
for opcode in (0x4890,0x48d0,0x4c90,0x4cd0):  # word/long, write/read (A0)
    results=[]
    for offset in (0x100000,0x180000):
        core.ctx=core.ram+offset
        state,ram=core.step(opcode,1,odd_address=True)
        sp=struct.unpack_from('<I',state,60)[0]
        assert sp==0x4700-14,(hex(opcode),hex(sp))
        assert struct.unpack_from('>I',ram,sp+10)[0]==0x104,(hex(opcode),ram[sp:sp+14].hex())
        assert struct.unpack_from('>I',ram,sp+2)[0]==0x4001
        assert struct.unpack_from('<I',state,64)[0]==0x200  # vector 3
        assert ram[0x4000:0x4008]==bytes((i*13+1)&255 for i in range(0x4000,0x4008))
        results.append((state,ram))
    assert results[0]==results[1],hex(opcode)
    # An aligned MOVEM takes no exception and advances past the register mask.
    state,_=core.step(opcode,1)
    assert struct.unpack_from('<I',state,60)[0]==0x4700
    assert struct.unpack_from('<I',state,64)[0]==0x104
print('PASS: MOVEM word/long read/write faults preserve guest PC across host relocation; aligned transfers return')
