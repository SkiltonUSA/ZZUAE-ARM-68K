#!/usr/bin/env python3
"""Exercise actual worker entry/exit and failure paths without private media.

Fault injection uses the compiled runtime exit, not a fake successful return.
This instruction-model test does not prove physical fault recovery.
"""
import struct
import subprocess
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UcError
from unicorn.arm_const import UC_CPU_ARM_CORTEX_A9, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'amiga/uae4arm'))
from elf import unpack

BASE = 0x12000040
SIZE = 0x2000000


def exercise(elf, case):
    image, relocations, _ = unpack(elf.read_bytes())
    for offset in relocations:
        value = struct.unpack_from('<I', image, offset)[0]
        struct.pack_into('<I', image, offset, value + BASE)
    symbols = {p[2]: int(p[0], 16) + BASE
               for line in subprocess.check_output(
                   ['/opt/homebrew/opt/llvm/bin/llvm-nm', str(elf)], text=True).splitlines()
               if len(p := line.split()) == 3}
    u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
    u.mem_map(BASE & ~4095, SIZE + 8192)
    u.mem_write(BASE, bytes(image))
    u.mem_map(0xf8f00000, 4096)
    u.mem_write(symbols['uae_shared'], struct.pack('<I', BASE))
    callback, result, end = BASE + 0x480000, BASE + 0x480200, BASE + 0x480100
    # stop() and clock() return zero, except the explicit cancellation case.
    u.mem_write(callback, bytes.fromhex('0100a0e31eff2fe1' if case == 'cancel' else '0000a0e31eff2fe1'))
    u.mem_write(callback + 16, bytes.fromhex('0000a0e31eff2fe1'))
    u.reg_write(UC_ARM_REG_SP, (BASE + SIZE - 8192) & ~15)
    u.reg_write(UC_ARM_REG_LR, end)
    for register, value in zip([UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3],
                               [0, result, callback, callback + 16]):
        u.reg_write(register, value)
    # A tiny original ROM boots a colour-register loop; no Kickstart/ADF needed.
    rom = bytearray(262144)
    struct.pack_into('>II', rom, 0, 0x20000, 0xfc0040)
    struct.pack_into('>HH', rom, 12, 34, 5)
    rom[64:74] = bytes.fromhex('33fc0f0000dff18060fe')
    u.mem_write(BASE + 0x4e0000, bytes(rom))
    u.mem_write(BASE + 0x482800, struct.pack('>I', 3))
    u.mem_write(BASE + 0x482814, struct.pack('>I', 2))
    table = None
    if 'zzuae_run_accelerated' in symbols:
        u.mem_write(BASE + 0x48282c, struct.pack('>I', 1))
        table = (BASE + 0x400000 + 16383) & ~16383
        for index, section in enumerate(range(BASE >> 20, ((BASE + SIZE - 1) >> 20) + 1)):
            leaf = table + 16384 + index * 1024
            u.mem_write(table + section * 4, struct.pack('<I', leaf | 1))
            for n in range(256):
                u.mem_write(leaf + n * 4, struct.pack('<I', (section << 20) + (n << 12) | 0x117))
    original_tables = bytes(u.mem_read(table, 0x10000)) if table else None
    if case == 'invalid-options':
        u.mem_write(BASE + 0x482804, struct.pack('>I', 0x80000000))
    if case == 'vector-rejected':
        # High vectors prevent installing the private VBAR; no guest starts.
        u.cpr_write(15, 0, 1, 0, 0, 0, False, 0x2000)
    injected = []
    if case == 'cleanup-abort':
        def fail_cleanup(uc, *_):
            injected.append(True)
            uc.reg_write(UC_ARM_REG_R0, 99)
            uc.reg_write(UC_ARM_REG_PC, symbols['exit'])
        address = symbols['_Z13compiler_exitv']
        u.hook_add(UC_HOOK_CODE, fail_cleanup, begin=address, end=address)
    try:
        u.emu_start(symbols['mesen_test'], end, count=200000000)
    except UcError:
        print('FAIL', case, 'cleanup injections', len(injected),
              'PC', hex(u.reg_read(UC_ARM_REG_PC)),
              'fatal_active', struct.unpack('<I', u.mem_read(symbols['uae_fatal_active'], 4))[0], flush=True)
        raise
    if case == 'cleanup-abort':
        assert len(injected) == 1, 'cleanup not reached exactly once'
    assert u.reg_read(UC_ARM_REG_PC) == end, 'worker did not return from ' + case
    expected = {'success': (0, 0), 'invalid-options': (10, 0), 'cancel': (2, 0),
                'cleanup-abort': (1, 99), 'vector-rejected': (1, 98)}[case]
    values = struct.unpack('<11I', u.mem_read(result, 44))
    assert (u.reg_read(UC_ARM_REG_R0), values[4]) == expected, (case, values)
    assert struct.unpack('<I', u.mem_read(symbols['uae_fatal_active'], 4))[0] == 0, 'fatal guard remains active: ' + case
    assert u.cpr_read(15, 0, 12, 0, 0, 0, False) == 0, 'VBAR not restored'
    if table and case in ('success', 'cancel'):
        assert bytes(u.mem_read(table, 0x10000)) == original_tables, 'executable page permissions not restored'
    if case == 'success':
        assert values[0] > 0 and values[9] == 3, 'synthetic ROM did not reach three frames'
    print('PASS', elf.name, case, flush=True)


if __name__ == '__main__':
    elf = Path(sys.argv[1])
    for case in sys.argv[2:]:
        exercise(elf, case)
