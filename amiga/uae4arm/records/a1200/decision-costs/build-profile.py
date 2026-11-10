from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='decision-phases';out=p/('build-'+variant);record=p.parent/'decision-costs'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
header=(p/'build-bitplane-span-profile/test-source/profile.h').read_text().replace('return *(volatile uint32_t*)0xf8f00200u;', 'asm volatile("" ::: "memory"); uint32_t t=*(volatile uint32_t*)0xf8f00200u; asm volatile("" ::: "memory"); return t;')
header=header.replace('ZU_PROFILE_STAGES 6u','ZU_PROFILE_STAGES 8u')
header+='\nstatic_assert(ZU_PROFILE_BASE+16*ZU_PROFILE_STAGES<=0x482980u,\"profile overlaps JIT report\");\n'
(b.SRC/'profile.h').write_text(header)
shutil.copy2(p/'build-bitplane-span-profile/test-source/profile.cpp',b.SRC/'profile.cpp')
f=out/'src/custom.cpp';original=f.read_text();s='#include "profile.h"\n'+original
start=s.index('STATIC_INLINE void finish_decisions (void)');end=s.index('/* Set the state of all decisions',start)
part=s[start:end];marker='STATIC_INLINE void finish_decisions (void)\n{';assert part.count(marker)==1
part=part.replace(marker,marker+'\n const bool sample=gp_choose();\n { GpScope calibration(7,sample); }\n GpScope total(0,sample);')
for stage,marker in [(1,'decide_diw (hpos);'),(2,'decide_line (hpos);'),(3,'decide_fetch (hpos);'),(4,'finish_final_fetch ();'),(5,'decide_sprites(-1, hpos + 1);')]:
 assert part.count(marker)==1,marker
 part=part.replace(marker,'{ GpScope phase('+str(stage)+',sample); '+marker+' }')
marker='\tdip = curr_drawinfo + next_lineno;';assert part.count(marker)==1
part=part.replace(marker,'\tGpScope record(6,sample);\n'+marker)
s=s[:start]+part+s[end:]
f.write_text(s);(record/'decision-phases.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/custom.cpp',tofile='profile/custom.cpp')))
for unit in ('events','custom','drawing','blitter','audio','disk'):
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src'/(unit+'.cpp')),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
f=out/'machine/host.c';s=f.read_text().replace('shared+0x482900u,96','shared+0x482900u,128').replace('stage<6;','stage<8;');f.write_text(s)
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
