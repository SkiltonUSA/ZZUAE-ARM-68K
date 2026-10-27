#!/usr/bin/env python3
"""Check the build's actual instruction audit without invoking a cross-build."""
import ast
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest

SOURCE = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] / 'scripts/build_uae4arm_machine.py'
TREE = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
AUDIT = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'audit_integer_context')


def audit(disassembly, neon=False):
    namespace = {'re': re, 'neon_experiment': neon,
                 'subprocess': SimpleNamespace(check_output=lambda *args, **kwargs:
                    disassembly if kwargs.get('text') else disassembly.encode())}
    # Execute the production function, preserving its filename/line locations
    # for coverage; the rest of the build script intentionally does not run.
    exec(compile(ast.Module(body=[AUDIT], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    namespace['audit_integer_context'](Path('worker.elf'))


class InstructionAudit(unittest.TestCase):
    def test_scalar_worker(self):
        audit('00000000 <worker>:\n       0: e0800001\tadd r0, r0, r1\n')

    def test_floating_point_is_rejected(self):
        for neon in (False, True):
            for instruction in ('vadd.f32 s0, s1, s2', 'vldr d0, [r0]', 'vpush {d8}'):
                with self.subTest(neon=neon, instruction=instruction):
                    with self.assertRaisesRegex(ValueError, 'Unsupported instruction'):
                        audit('00000000 <worker>:\n       0: 12345678\t' + instruction + '\n', neon)

    def test_only_audited_simd_leaves_are_allowed(self):
        for function in ('zu_neon_available', 'zu_neon_snapshot', 'zu_convert_neon', 'zu_bitplane_neon'):
            code = '00000000 <' + function + '>:\n       0: 12345678\tvorr q0, q1, q2\n'
            audit(code, True)
            with self.assertRaises(ValueError):
                audit(code, False)
        for function in ('zu_convert_neon_extra', 'zu_bitplane_neon_extra', 'other_function'):
            with self.assertRaises(ValueError):
                audit('00000000 <' + function + '>:\n       0: 12345678\tvorr q0, q1, q2\n', True)

    def test_next_function_is_not_exempt(self):
        with self.assertRaises(ValueError):
            audit('00000000 <zu_convert_neon>:\n       0: 12345678\tvorr q0, q1, q2\n'
                  '00000004 <worker>:\n       4: 12345678\tvadd.f32 s0, s1, s2\n', True)

    def test_hardware_divide_is_rejected_even_inside_simd_leaf(self):
        for instruction in ('sdiv', 'udiv'):
            for neon in (False, True):
                with self.subTest(instruction=instruction, neon=neon):
                    with self.assertRaises(ValueError):
                        audit('00000000 <zu_convert_neon>:\n       0: 12345678\t' + instruction + ' r0, r1, r2\n', neon)


if __name__ == '__main__':
    unittest.main()
