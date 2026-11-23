from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='denise-once';out=p/('build-'+variant);record=p.parent/'bitplane-spans'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());f=out/'src/custom.cpp';s=f.read_text();original=s
start=s.index('STATIC_INLINE void beginning_of_plane_block_x');end=s.index('static void beginning_of_plane_block_0',start)
block=s[start:end];assert block.count('compute_toscr_delay (hpos,')==2
block=block.replace('compute_toscr_delay (hpos, bplcon1)', 'compute_toscr_delay_1 (bplcon1)').replace('compute_toscr_delay (hpos, bplcon1t)', 'compute_toscr_delay_1 (bplcon1t)')
s=s[:start]+block+s[end:];f.write_text(s)
(record/'denise.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/custom.cpp',tofile='candidate/custom.cpp')))
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'custom.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
