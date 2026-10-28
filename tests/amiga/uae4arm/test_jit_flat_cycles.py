"""Precomputed opcode classification must match the existing lookup exactly."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).absolute().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from prepare_uae4arm_jit_timing import timing_header


class FlatCycleTests(unittest.TestCase):
    def test_every_opcode_and_reinitialization(self):
        cpu = ''.join('uae_u32 REGPARAM2 CPUFUNC(op_%04x_0)(uae_u32 opcode) {return %s;}' % (op, cost)
                      for op, cost in [(0, '4 * CYCLE_UNIT / 2'), (0x5280, '4 * CYCLE_UNIT / 2'),
                                       (0xffff, '8 * CYCLE_UNIT / 2'), (0x51c8, 'count_cycles')])
        table = 'CPUFUNC(op_smalltbl_3)[] = {' + ''.join(
            '{ CPUFUNC(op_%04x_0), 0x%04x },' % (op, op) for op in [0, 0x5280, 0xffff, 0x51c8]) + '};'
        original = timing_header(cpu, table).replace('zzuae_constant_cycles', 'reference_cycles')
        flat = timing_header(cpu, table, flat=True)
        source = 'struct {int handler;} table68k[65536];\n' + original + flat + r'''
int main() {
 const int aliases[] = {-1, 0, 0x5280, 0xffff, 0x51c8, 0x1234};
 for (unsigned pass=0; pass<3; ++pass) {
  for (unsigned op=0; op<65536; ++op)
   table68k[op].handler = pass==0 ? -1 : aliases[(op+pass)%6];
  zzuae_prepare_cycle_map();
  for (unsigned op=0; op<65536; ++op)
   if (zzuae_constant_cycles(op)!=reference_cycles(op)) return 1;
 }
 return 0;
}
'''
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder / 'test.cpp').write_text(source)
            subprocess.run(['clang++', '-std=c++11', '-fsanitize=undefined', str(folder / 'test.cpp'), '-o', str(folder / 'test')], check=True)
            subprocess.run([str(folder / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
