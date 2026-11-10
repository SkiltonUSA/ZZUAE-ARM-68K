from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='special-counts';out=p/('build-'+variant)
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
for name in ('profile.h','profile.cpp'):shutil.copy2(p/'build-bitplane-span-profile/test-source'/name,b.SRC/name)
f=out/'src/newcpu.cpp';original=f.read_text();marker='static int do_specialties (int cycles)\n{';assert original.count(marker)==1
s='#include "profile.h"\n'+original.replace(marker,marker+'''
 if(timeframes>=3000) {
  unsigned flags=regs.spcflags;
  ++zu_profile_calls[0];
  unsigned category=flags==SPCFLAG_END_COMPILE?1:
   flags==SPCFLAG_BLTNASTY?2:flags==SPCFLAG_COPPER?3:
   (flags==SPCFLAG_INT || flags==SPCFLAG_DOINT)?4:5;
  ++zu_profile_calls[category];
 }
''');f.write_text(s)
(p.parent/'special-fast/counts.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/newcpu.cpp',tofile='counts/newcpu.cpp')))
subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/'newcpu.o')],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
