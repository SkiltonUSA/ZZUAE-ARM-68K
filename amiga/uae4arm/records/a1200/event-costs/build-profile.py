from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='event-profile';out=p/('build-'+variant);record=p.parent/'event-costs'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
header=(p/'build-bitplane-span-profile/test-source/profile.h').read_text().replace('return *(volatile uint32_t*)0xf8f00200u;', 'asm volatile("" ::: "memory"); uint32_t t=*(volatile uint32_t*)0xf8f00200u; asm volatile("" ::: "memory"); return t;')
header=header.replace('ZU_PROFILE_STAGES 6u','ZU_PROFILE_STAGES 8u')
header+='\nstatic_assert(ZU_PROFILE_BASE+16*ZU_PROFILE_STAGES<=0x482980u,\"profile overlaps JIT report\");\n'
(b.SRC/'profile.h').write_text(header)
shutil.copy2(p/'build-bitplane-span-profile/test-source/profile.cpp',b.SRC/'profile.cpp')
f=out/'src/events.cpp';original=f.read_text();s='#include "profile.h"\n'+original
marker='void events_schedule (void)\n{';assert s.count(marker)==1
s=s.replace(marker,marker+'\n GpScope schedule(7,gp_choose());')
marker='(*eventtab[i].handler)();';assert s.count(marker)==2
s=s.replace(marker,'{ GpScope callback(i,gp_choose()); '+marker+' }')
f.write_text(s);(record/'events.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/events.cpp',tofile='profile/events.cpp')))
for unit in ('events','custom','drawing','blitter','audio','disk'):
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src'/(unit+'.cpp')),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
f=out/'machine/host.c';s=f.read_text().replace('shared+0x482900u,96','shared+0x482900u,128').replace('stage<6;','stage<8;');f.write_text(s)
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
