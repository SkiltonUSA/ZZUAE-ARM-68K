from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='blitter-flag-fast';out=p/('build-'+variant)
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text())
f=out/'src/newcpu.cpp';original=f.read_text()
marker='   if(regs.spcflags && !regs.halted)do_specialties(0);'
assert original.count(marker)==1
s=original.replace(marker,'   /* At zero cycles, BLTNASTY alone performs no service. Keep it pending. */\n   if(regs.spcflags && regs.spcflags!=SPCFLAG_BLTNASTY && !regs.halted)do_specialties(0);');f.write_text(s)
(p.parent/'blitter-service/candidate.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/newcpu.cpp',tofile='candidate/newcpu.cpp')))
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'newcpu.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
