from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='special-fast';out=p/('build-'+variant)
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/newcpu.cpp';original=f.read_text();marker='static int do_specialties (int cycles)\n{';assert original.count(marker)==1
s=original.replace(marker,marker+'''
#ifdef JIT
 /* No other service is pending: END_COMPILE has already done its job. */
 if (regs.spcflags == SPCFLAG_END_COMPILE) {
  unset_special(SPCFLAG_END_COMPILE);
  return 0;
 }
#endif
''');f.write_text(s)
(p.parent/'special-fast/candidate.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/newcpu.cpp',tofile='candidate/newcpu.cpp')))
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'newcpu.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
