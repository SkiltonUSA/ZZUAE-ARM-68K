from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';base=p/'build-pixel4';out=p/'build-remaining-profile'
shutil.copytree(base,out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
f=b.SRC/'profile.h';s=f.read_text();s=s.replace('struct ZuProfileScope {','''extern unsigned long timeframes;
extern uint32_t gp_rng[ZU_PROFILE_STAGES];
static bool gp_choose(unsigned s){
 if(timeframes<3000)return false;
 uint32_t &r=gp_rng[s];r^=r<<13;r^=r>>17;r^=r<<5;return (r&63u)==0;
}
struct ZuProfileScope {''')
s=s.replace('unsigned stage; uint32_t start;', 'unsigned stage; bool active; uint32_t start;').replace('stage(s),start(zu_profile_now()){}', 'stage(s),active(gp_choose(s)),start(active?zu_profile_now():0){}').replace('~ZuProfileScope(){zu_profile_ticks', '~ZuProfileScope(){if(!active)return;zu_profile_ticks')
s=s.replace('#define ZU_PROFILE(stage) ZuProfileScope zu_profile_scope(stage)', '#define ZU_PROFILE(stage) ((void)0)\n#define GP_PROFILE(stage) ZuProfileScope gp_scope(stage)');f.write_text(s)
f=b.SRC/'profile.cpp';f.write_text(f.read_text()+'\nuint32_t gp_rng[6]={0x73c4a921,0x87654321,0x2917bb13,0x81517a31,0x12345678,0x78de2191};\n')
cases={'custom':[('static void decide_diw (int hpos)',0),('static void remember_ctable (void)',1),('static void decide_sprites(int spnr, int hpos, bool quick)',2),('static void do_playfield_collisions (void)',3),('static void do_sprite_collisions (void)',4),('static void do_sprites (int hpos)',5)]}
for unit,functions in cases.items():
 f=out/'src'/(unit+'.cpp');s=f.read_text()
 if '#include "profile.h"' not in s:s='#include "profile.h"\n'+s
 for name,stage in functions:
  start=s.index(name+'\n{')+len(name+'\n{');s=s[:start]+f'\n GP_PROFILE({stage});'+s[start:]
 f.write_text(s)
for unit in ['custom','blitter','audio','disk','drawing']:
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src'/(unit+'.cpp')),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('remaining-profile',):").replace("a1200/performance/build-", "a1200/gameplay/build-"))
