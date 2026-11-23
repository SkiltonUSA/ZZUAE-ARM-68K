from pathlib import Path
import sys, json, subprocess, runpy
sys.path.insert(0, 'scripts')
import build_uae4arm as b
p = b.OUT / 'a1200/gameplay'
variant = 'fetch-fused'
out = p / ('build-' + variant)
b.OUT = out
b.SRC = out / 'test-source'
b.prepare = lambda: out / 'src'
c = json.loads((out / 'compile.json').read_text())
subprocess.run([*b.RUN, 'arm-none-eabi-g++', *c['flags'], '-c',
                b.inside(out / 'src/custom.cpp'), '-o', b.inside(out / 'custom.o')], check=True)
sys.argv = ['build_uae4arm_machine.py', '--guest-jit', '--hardware']
runpy.run_path('scripts/build_uae4arm_machine.py', run_name='__main__')
sys.argv = ['lock-input.py', variant]
runpy.run_path(str(p.parent / 'sprite-decisions/lock-input.py'), run_name='__main__')
