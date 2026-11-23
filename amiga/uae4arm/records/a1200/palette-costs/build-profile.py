from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='palette-profile';out=p/('build-'+variant);record=p.parent/'palette-costs'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
header=(p/'build-bitplane-span-profile/test-source/profile.h').read_text().replace('return *(volatile uint32_t*)0xf8f00200u;', 'asm volatile("" ::: "memory"); uint32_t t=*(volatile uint32_t*)0xf8f00200u; asm volatile("" ::: "memory"); return t;')
(b.SRC/'profile.h').write_text(header)
shutil.copy2(p/'build-bitplane-span-profile/test-source/profile.cpp',b.SRC/'profile.cpp')
for unit in ('custom','drawing'):
 f=out/'src'/(unit+'.cpp');original=f.read_text();s='#include "profile.h"\n'+original
 if unit=='custom':
  marker='static void remember_ctable (void)\n{';assert s.count(marker)==1
  s=s.replace(marker,marker+'\n const bool sample=gp_choose();\n { GpScope calibration(5,sample); }\n GpScope total(0,sample);')
  marker='\t\tcolor_reg_cpy (curr_color_tables + next_color_entry, &current_colors);';assert s.count(marker)==1
  s=s.replace(marker,'{ GpScope copy(1,sample);\n'+marker+'\n}')
  start=s.index('static void reset_decisions (void)');end=s.index('  last_decide_line_hpos = -1;',start)
  part=s[start:end];part=part.replace('\tmemset (outword, 0, sizeof outword);','\t{ GpScope clear(4,gp_choose());\n\tmemset (outword, 0, sizeof outword);');part+='\n }\n';s=s[:start]+part+s[end:]
 else:
  marker='static void adjust_drawing_colors (int ctable, int need_full)\n{';assert s.count(marker)==1
  s=s.replace(marker,marker+'\n const bool sample=gp_choose();\n GpScope total(2,sample);')
  marker='\t\t\tmemcpy (colors_for_drawing.acolors, curr_color_tables[ctable].acolors,\n\t\t\tsizeof colors_for_drawing.acolors);';assert s.count(marker)==1
  s=s.replace(marker,'{ GpScope copy(3,sample);\n'+marker+'\n}')
 f.write_text(s);(record/(unit+'.patch')).write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/'+unit+'.cpp',tofile='profile/'+unit+'.cpp')))
for unit in ('custom','drawing','blitter','audio','disk'):
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src'/(unit+'.cpp')),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
