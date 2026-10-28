"""Identify constant-cycle handlers in the pinned 68020 interpreter table.

Only the isolated instruction-timing build uses this map. Variable-cycle
instructions execute in the interpreter so their runtime cycle count survives.
"""
import re


def constant_cycle_map(cpu, tables):
    functions = re.split(
        r'uae_u32 REGPARAM2 CPUFUNC\((op_[0-9a-f]+_\d+)\)\(uae_u32 opcode\)', cpu)
    constant = set()
    for name, body in zip(functions[1::2], functions[2::2]):
        returns = set(re.findall(r'\breturn\s+([^;]+);', body))
        if len(returns) == 1 and re.fullmatch(
                r'\d+\s*\*\s*CYCLE_UNIT\s*/\s*2', next(iter(returns)).strip()):
            constant.add(name)
    table = tables.split('CPUFUNC(op_smalltbl_3)[] = {', 1)[1].split('};', 1)[0]
    entries = re.findall(r'CPUFUNC\((op_[0-9a-f]+_\d+)\),\s*0x([0-9a-f]+)', table)
    if not entries:
        raise ValueError('68020 interpreter table is missing')
    bits = bytearray(8192)
    for name, opcode in entries:
        op = int(opcode, 16)
        if name in constant:
            bits[op >> 3] |= 1 << (op & 7)
    return bytes(bits)


def timing_header(cpu, tables, flat=False):
    bits = constant_cycle_map(cpu, tables)
    rows = [','.join(str(n) for n in bits[i:i+32]) for i in range(0, len(bits), 32)]
    header = '''#pragma once
// Generated from the pinned 68020 interpreter cycle returns.
static bool zzuae_constant_cycles(unsigned opcode) {
 static const unsigned char bits[8192]={
''' + ',\n'.join(rows) + '''
 };
 int canonical=table68k[opcode].handler;
 if(canonical>=0)opcode=(unsigned)canonical;
 return (bits[opcode>>3] & (1u<<(opcode&7)))!=0;
}
'''
    if not flat:
        return header
    return header.replace('zzuae_constant_cycles', 'zzuae_canonical_cycles') + """
// CPU setup resolves aliases once. Rebuild after read_table68k/do_merges.
static unsigned char zzuae_cycle_map[8192];
static void zzuae_prepare_cycle_map() {
 for (unsigned byte=0; byte<8192; ++byte) {
  unsigned value=0;
  for (unsigned bit=0; bit<8; ++bit)
   if (zzuae_canonical_cycles(byte*8+bit)) value|=1u<<bit;
  zzuae_cycle_map[byte]=(unsigned char)value;
 }
}
static bool zzuae_constant_cycles(unsigned opcode) {
 return (zzuae_cycle_map[opcode>>3] & (1u<<(opcode&7)))!=0;
}
"""
