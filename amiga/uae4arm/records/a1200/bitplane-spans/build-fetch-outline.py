from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib,re
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='fetch-outline';out=p/('build-'+variant);record=p.parent/'bitplane-spans'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());f=out/'src/custom.cpp';s=f.read_text();original=s
marker='STATIC_INLINE int one_fetch_cycle_0 (int pos, int ddfstop_to_test, int dma, int fm)'
s=s.replace(marker,'''/* Private code-size experiment: preserve fetch semantics, share AGA64 code. */
static __attribute__((noinline,noclone)) void zz_fetch64(int nr) { fetch(nr,2); }
STATIC_INLINE void zz_fetch_cycle_plane(int nr,int fm) {
    if(fm==2)zz_fetch64(nr);else fetch(nr,fm);
}
'''+marker)
a=s.index(marker);z=s.index('static int one_fetch_cycle_fm0',a);part=s[a:z];assert len(re.findall(r'\bfetch \(',part))==14
part=re.sub(r'\bfetch \(', 'zz_fetch_cycle_plane (',part);s=s[:a]+part+s[z:];f.write_text(s)
(record/'fetch-outline.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/custom.cpp',tofile='candidate/custom.cpp')))
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'custom.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
