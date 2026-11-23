from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='sprite-attachment';out=p/('build-'+variant);record=p.parent/'sprite-decisions'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());f=out/'src/custom.cpp';s=f.read_text();original=s
a=s.index('\t\tuae_u8 *stb1 = spixstate.bytes + word_offs;');z=s.index('\n\t\te->has_attached = 1;',a)
s=s[:a]+(record/'attachment.inc').read_text().replace('ORIGINAL',s[a:z])+s[z:];f.write_text(s)
(record/'attachment.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/custom.cpp',tofile='candidate/custom.cpp')))
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'custom.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(record/'lock-input.py'),run_name='__main__')
