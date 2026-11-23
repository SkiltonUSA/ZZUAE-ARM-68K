from pathlib import Path
import sys, shutil, json, subprocess, runpy, difflib

sys.path.insert(0, 'scripts')
import build_uae4arm as b

p = b.OUT / 'a1200/gameplay'
variant = 'fetch-table'
out = p / ('build-' + variant)
record = p.parent / 'bitplane-spans'
shutil.copytree(p / 'build-pixel4', out, dirs_exist_ok=True)
b.OUT = out
b.SRC = out / 'test-source'
b.prepare = lambda: out / 'src'
c = json.loads((out / 'compile.json').read_text())
f = out / 'src/custom.cpp'
original = f.read_text()
start = original.index('\t\tswitch (fm_maxplane) {', original.index('STATIC_INLINE int one_fetch_cycle_0'))
end = original.index('\n\t}\n\n\tif (bpl1dat_written)', start)
replacement = '''        const int *sequence = 0;
        switch (fm_maxplane) {
            case 8: sequence = cycle_sequences + 16; break;
            case 4: sequence = cycle_sequences + 8; break;
            case 2: sequence = cycle_sequences; break;
        }
        if (sequence && cycle_start < fm_maxplane)
            fetch(sequence[cycle_start] - 1, fm);'''
s = original[:start] + replacement + original[end:]
f.write_text(s)
(record / 'fetch-table.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(True), s.splitlines(True),
    fromfile='reference/custom.cpp', tofile='candidate/custom.cpp')))
subprocess.run([*b.RUN, 'arm-none-eabi-g++', *c['flags'], '-c',
                b.inside(f), '-o', b.inside(out / 'custom.o')], check=True)
sys.argv = ['build_uae4arm_machine.py', '--guest-jit', '--hardware']
runpy.run_path('scripts/build_uae4arm_machine.py', run_name='__main__')
sys.argv = ['lock-input.py', variant]
runpy.run_path(str(p.parent / 'sprite-decisions/lock-input.py'), run_name='__main__')
