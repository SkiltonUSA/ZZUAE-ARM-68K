from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='blitter-service';out=p/('build-'+variant);record=p.parent/'blitter-service'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
for name in ('profile.h','profile.cpp'):shutil.copy2(p/'build-palette-profile/test-source'/name,b.SRC/name)
for unit in ('blitter','newcpu'):
 f=out/'src'/(unit+'.cpp');original=f.read_text();s='#include "profile.h"\n'+original
 if unit=='blitter':
  start=s.index('int blitnasty (void)');end=s.index('/* very approximate',start);part=s[start:end]
  part=part.replace('int cycles, ccnt;', 'int cycles, ccnt;\n const bool sample=gp_choose();\n {GpScope floor(5,sample);}\n GpScope total(0,sample);')
  part=part.replace('if (bltstate == BLT_done)\n\t\treturn 0;', 'if (bltstate == BLT_done) {if(sample)++zu_profile_calls[3];return 0;}')
  part=part.replace('if (blit_last_cycle >= blit_diag[0] && blit_dmacount == blit_diag[0])\n\t\treturn 0;', 'if (blit_last_cycle >= blit_diag[0] && blit_dmacount == blit_diag[0]) {if(sample)++zu_profile_calls[4];return 0;}')
  part=part.replace('while (blit_last_cycle < cycles) {','{ GpScope slots(1,sample && blit_last_cycle<cycles);\n\twhile (blit_last_cycle < cycles) {').replace('\treturn ccnt;', '\t}\n\treturn ccnt;')
  s=s[:start]+part+s[end:]
 else:
  start=s.index('static int do_specialties (int cycles)');end=s.index('/* It\'s really sad',start);part=s[start:end]
  marker='\t  x_do_cycles (c * CYCLE_UNIT);';assert part.count(marker)==1
  part=part.replace(marker,'{ GpScope events(2,gp_choose());\n'+marker+'\n}')
  s=s[:start]+part+s[end:]
 f.write_text(s);(record/(unit+'.patch')).write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/'+unit+'.cpp',tofile='profile/'+unit+'.cpp')))
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(f),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
