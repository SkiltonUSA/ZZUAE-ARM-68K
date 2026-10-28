"""Cycle classification must reject variable costs and unknown handlers."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
from prepare_uae4arm_jit_timing import constant_cycle_map, timing_header


class TimingMapTests(unittest.TestCase):
    def classify(self, body, name='op_5280_0'):
        cpu=f'uae_u32 REGPARAM2 CPUFUNC({name})(uae_u32 opcode) {{ {body} }}'
        table=f'CPUFUNC(op_smalltbl_3)[] = {{\n{{ CPUFUNC(op_5280_0), 0x5280, 2 }},\n}};'
        return constant_cycle_map(cpu,table)[0x5280 >> 3] & 1

    def test_constant(self):
        self.assertEqual(self.classify('return 4 * CYCLE_UNIT / 2;'),1)

    def test_same_cost_on_both_paths(self):
        self.assertEqual(self.classify('if(opcode) return 4 * CYCLE_UNIT / 2; return 4 * CYCLE_UNIT / 2;'),1)

    def test_branch_costs(self):
        self.assertEqual(self.classify('if(opcode) return 9 * CYCLE_UNIT / 2; return 5 * CYCLE_UNIT / 2;'),0)

    def test_computed_cost(self):
        self.assertEqual(self.classify('return 4 * CYCLE_UNIT / 2 + count_cycles;'),0)

    def test_unknown_handler(self):
        self.assertEqual(self.classify('return 4 * CYCLE_UNIT / 2;','op_5280_2'),0)

    def test_missing_returns(self):
        self.assertEqual(self.classify('abort();'),0)

    def test_missing_table(self):
        with self.assertRaises(ValueError):
            constant_cycle_map('', 'CPUFUNC(op_smalltbl_3)[] = {};')

    def test_other_cpu_table_is_excluded(self):
        cpu='uae_u32 REGPARAM2 CPUFUNC(op_5280_0)(uae_u32 opcode) {return 4 * CYCLE_UNIT / 2;}'
        tables='CPUFUNC(op_smalltbl_3)[] = {{ CPUFUNC(op_5280_0), 0x5280 }};'
        tables+='CPUFUNC(op_smalltbl_4)[] = {{ CPUFUNC(op_5280_0), 0x51c8 }};'
        self.assertEqual(constant_cycle_map(cpu,tables)[0x51c8 >> 3],0)

    def test_header_compiles_and_resolves_aliases(self):
        import subprocess,tempfile
        cpu='uae_u32 REGPARAM2 CPUFUNC(op_5280_0)(uae_u32 opcode) {return 4 * CYCLE_UNIT / 2;}'
        table='CPUFUNC(op_smalltbl_3)[] = {{ CPUFUNC(op_5280_0), 0x5280 }};'
        source='struct {int handler;} table68k[65536];\n'+timing_header(cpu,table)+'''
int main(){
 for(auto &entry:table68k)entry.handler=-1;
 table68k[0x5281].handler=0x5280;
 return !zzuae_constant_cycles(0x5280) || !zzuae_constant_cycles(0x5281) || zzuae_constant_cycles(0x51c8);
}
'''
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);(path/'test.cpp').write_text(source)
            subprocess.run(['c++','-std=c++11',str(path/'test.cpp'),'-o',str(path/'test')],check=True)
            subprocess.run([str(path/'test')],check=True)


if __name__=='__main__':unittest.main()
