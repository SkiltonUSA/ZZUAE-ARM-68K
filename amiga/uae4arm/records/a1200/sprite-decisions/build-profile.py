from pathlib import Path
import sys,shutil,json,subprocess,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';out=p/'build-sprite-decision-profile'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
f=b.SRC/'profile.h';s=f.read_text();a=s.index('struct ZuProfileScope {');z=s.index('void zu_profile_finish',a)
s=s[:a]+'''extern unsigned long timeframes;
extern uint32_t gp_rng[6];
extern bool gp_sprite_record;
static bool gp_choose(unsigned s){
 if(timeframes<3000)return false;
 uint32_t &r=gp_rng[s];r^=r<<13;r^=r>>17;r^=r<<5;return (r&63u)==0;
}
struct GpScope {
 unsigned stage; bool active; uint32_t start;
 GpScope(unsigned s,bool a):stage(s),active(a),start(a?zu_profile_now():0){}
 ~GpScope(){if(active){zu_profile_ticks[stage]+=(uint32_t)(zu_profile_now()-start);zu_profile_calls[stage]++;}}
};
#define ZU_PROFILE(stage) ((void)0)
'''+s[z:];f.write_text(s)
f=b.SRC/'profile.cpp';f.write_text(f.read_text()+'\nuint32_t gp_rng[6]={0x73c4a921,0x87654321,0x2917bb13,0x81517a31,0x12345678,0x78de2191};\nbool gp_sprite_record;\n')
f=out/'src/custom.cpp';s=f.read_text();s='#include "profile.h"\n'+s
name='static void decide_sprites(int spnr, int hpos, bool quick)\n{';start=s.index(name)+len(name);s=s[:start]+'\n const bool sample=gp_choose(0); GpScope total(0,sample);'+s[start:]
a=s.index(name);z=s.index('\nSTATIC_INLINE void decide_sprites',a);part=s[a:z]
part=part.replace('if (!quick) {','if (!quick) {\n    GpScope preparation(1,sample);')
part=part.replace('count = 0;','count = 0;\n { GpScope scan(2,sample);')
part=part.replace('\n\tfor (i = 0; i < count; i++) {','\n }\n { GpScope records(3,sample && count>0);\n gp_sprite_record=sample;\n\tfor (i = 0; i < count; i++) {')
part=part.replace('\n\tlast_sprite_point = point;', '\n gp_sprite_record=false;\n }\n\tlast_sprite_point = point;');s=s[:a]+part+s[z:]
a=s.index('static void record_sprite_1 (');a=s.index('{',a)+1;s=s[:a]+'\n GpScope pixels(5,gp_sprite_record);'+s[a:]
name='static void do_sprites (int hpos)\n{';a=s.index(name)+len(name);s=s[:a]+'\n GpScope dma(4,gp_choose(4));'+s[a:];f.write_text(s)
for unit in ['custom','blitter','audio','disk','drawing']:
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src'/(unit+'.cpp')),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
exec((b.ROOT/'.context/amiga/uae4arm/a1200/performance/extend-chipreads.py').read_text().replace("for variant in ('chipreads',):", "for variant in ('sprite-decision-profile',):").replace('a1200/performance/build-','a1200/gameplay/build-'))
