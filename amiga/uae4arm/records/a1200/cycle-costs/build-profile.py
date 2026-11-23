from pathlib import Path
import sys, shutil, json, subprocess, runpy, difflib

sys.path.insert(0, 'scripts')
import build_uae4arm as b

p = b.OUT / 'a1200/gameplay'
variant = 'fetch-cycle-profile'
out = p / ('build-' + variant)
record = p.parent / 'cycle-costs'
shutil.copytree(p / 'build-pixel4', out, dirs_exist_ok=True)
b.OUT = out
b.SRC = out / 'test-source'
b.prepare = lambda: out / 'src'
c = json.loads((out / 'compile.json').read_text())
c['flags'] = ['-I' + b.inside(b.SRC)] + c['flags'] + ['-DZZUAE_PROFILE']
(out / 'compile.json').write_text(json.dumps(c))
previous = p.parent / 'bitplane-spans'
header = (p / 'build-bitplane-span-profile/test-source/profile.h').read_text()
header = header.replace('return *(volatile uint32_t*)0xf8f00200u;',
    'asm volatile("" ::: "memory"); uint32_t t=*(volatile uint32_t*)0xf8f00200u; asm volatile("" ::: "memory"); return t;')
(b.SRC / 'profile.h').write_text(header)
shutil.copy2(p / 'build-bitplane-span-profile/test-source/profile.cpp', b.SRC / 'profile.cpp')
f = out / 'src/custom.cpp'
original = f.read_text()
s = '#include "profile.h"\n' + original
marker = 'STATIC_INLINE void update_fetch (int until, int fm)\n{'
assert s.count(marker) == 1
s = s.replace(marker, marker + '\n const bool sample=gp_choose(); GpFetch context(sample);')
marker = 'STATIC_INLINE int one_fetch_cycle_0 (int pos, int ddfstop_to_test, int dma, int fm)\n{'
start = s.index(marker)
end = s.index('static int one_fetch_cycle_fm0', start)
part = s[start:end]
part = part.replace(marker, marker + '''
 const bool sample=gp_active;
 { GpScope calibration(5,sample); }
 GpScope total(0,sample);
 { GpScope events(1,sample);''', 1)
part = part.replace('\n\tif (dma && plf_state != plf_wait_stop) {',
    '\n }\n { GpScope dispatch(2,sample);\n\tif (dma && plf_state != plf_wait_stop) {', 1)
part = part.replace('\n\tif (bpl1dat_written) {',
    '\n }\n GpScope output(3,sample);\n\tif (bpl1dat_written) {', 1)
s = s[:start] + part + s[end:]
start = s.index('STATIC_INLINE void fetch (int nr, int fm)')
end = s.index('STATIC_INLINE void toscr_3_ecs', start)
part = s[start:end]
part = part.replace('    switch (fm)', '    { GpScope memory(4,gp_active);\n    switch (fm)', 1)
part = part.replace('    if (plf_state == plf_passed_stop2', '    }\n    if (plf_state == plf_passed_stop2', 1)
s = s[:start] + part + s[end:]
f.write_text(s)
(record / 'profile.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(True), s.splitlines(True), fromfile='reference/custom.cpp', tofile='profile/custom.cpp')))
for unit in ('custom', 'blitter', 'audio', 'disk', 'drawing'):
    subprocess.run([*b.RUN, 'arm-none-eabi-g++', *c['flags'], '-c',
                    b.inside(out / 'src' / (unit + '.cpp')), '-o', b.inside(out / (unit + '.o'))], check=True)
sys.argv = ['build_uae4arm_machine.py', '--guest-jit', '--hardware']
runpy.run_path('scripts/build_uae4arm_machine.py', run_name='__main__')
sys.argv = ['lock-input.py', variant]
runpy.run_path(str(p.parent / 'sprite-decisions/lock-input.py'), run_name='__main__')
