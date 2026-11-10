from pathlib import Path
import sys, shutil, json, subprocess, runpy, difflib

sys.path.insert(0, 'scripts')
import build_uae4arm as b

p = b.OUT / 'a1200/gameplay'
variant = 'scroll-cache'
out = p / ('build-' + variant)
record = p.parent / variant
shutil.copytree(p / 'build-pixel4', out, dirs_exist_ok=True)
b.OUT = out
b.SRC = out / 'test-source'
b.prepare = lambda: out / 'src'
c = json.loads((out / 'compile.json').read_text())
f = out / 'src/custom.cpp'
original = f.read_text()
a = original.index('STATIC_INLINE void compute_toscr_delay_1 (int bplcon1)')
z = original.index('STATIC_INLINE void compute_toscr_delay (', a)
part=original[a:z]
x=part.index('{')+1;y=part.rindex('}')
part=part[:x]+'\n'+(record/'entry.inc').read_text()+part[x:y]+(record/'exit.inc').read_text()+part[y:]
s=original[:a]+part+original[z:]
f.write_text(s)
(record / 'candidate.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(True), s.splitlines(True), fromfile='reference/custom.cpp', tofile='candidate/custom.cpp')))
subprocess.run([*b.RUN, 'arm-none-eabi-g++', *c['flags'], '-c',
                b.inside(f), '-o', b.inside(out / 'custom.o')], check=True)
sys.argv = ['build_uae4arm_machine.py', '--guest-jit', '--hardware']
runpy.run_path('scripts/build_uae4arm_machine.py', run_name='__main__')
sys.argv = ['lock-input.py', variant]
runpy.run_path(str(p.parent / 'sprite-decisions/lock-input.py'), run_name='__main__')
