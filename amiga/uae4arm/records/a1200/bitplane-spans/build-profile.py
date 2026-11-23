from pathlib import Path
import sys,shutil,json,subprocess,runpy,difflib
sys.path.insert(0,'scripts')
import build_uae4arm as b
p=b.OUT/'a1200/gameplay';variant='bitplane-span-profile';out=p/('build-'+variant);record=p.parent/'bitplane-spans'
shutil.copytree(p/'build-pixel4',out,dirs_exist_ok=True)
b.OUT=out;b.SRC=out/'test-source';b.prepare=lambda:out/'src'
c=json.loads((out/'compile.json').read_text());c['flags']=['-I'+b.inside(b.SRC)]+c['flags']+['-DZZUAE_PROFILE'];(out/'compile.json').write_text(json.dumps(c))
f=b.SRC/'profile.h';s=f.read_text();a=s.index('struct ZuProfileScope {');z=s.index('void zu_profile_finish',a)
s=s[:a]+'''extern unsigned long timeframes;
extern uint32_t gp_rng;
extern bool gp_active;
static bool gp_choose(){
 if(timeframes<3000)return false;
 gp_rng^=gp_rng<<13;gp_rng^=gp_rng>>17;gp_rng^=gp_rng<<5;return (gp_rng&63u)==0;
}
struct GpScope {
 unsigned stage; bool active; uint32_t start;
 GpScope(unsigned s,bool a):stage(s),active(a),start(a?zu_profile_now():0){}
 ~GpScope(){if(active){zu_profile_ticks[stage]+=(uint32_t)(zu_profile_now()-start);zu_profile_calls[stage]++;}}
};
struct GpFetch {
 bool saved;
 GpFetch(bool a):saved(gp_active){gp_active=a;}
 ~GpFetch(){gp_active=saved;}
};
#define ZU_PROFILE(stage) ((void)0)
'''+s[z:];f.write_text(s)
f=b.SRC/'profile.cpp';f.write_text(f.read_text()+'\nuint32_t gp_rng=0x73c4a921;\nbool gp_active;\n')
f=out/'src/custom.cpp';original=f.read_text();s='#include "profile.h"\n'+original
name='STATIC_INLINE void update_fetch (int until, int fm)\n{';a=s.index(name)+len(name);s=s[:a]+'\n const bool sample=gp_choose(); GpFetch context(sample); GpScope total(0,sample);'+s[a:]
a=s.index(name);z=s.index('static void update_fetch_0',a);part=s[a:z]
part=part.replace('\tfor (; ; pos++) {',' { GpScope preparation(1,sample);\n\tfor (; ; pos++) {',1)
part=part.replace('\n\t// vdiw getting cleared','\n }\n\t// vdiw getting cleared',1)
part=part.replace('\t\t\tdo_long_fetch (count >> (3 - toscr_res), dma, fm);','\t\t\t{ GpScope bulk(2,sample); do_long_fetch (count >> (3 - toscr_res), dma, fm); }')
part=part.replace('\tfor (; pos < until; pos++) {',' { GpScope tail(3,sample);\n\tfor (; pos < until; pos++) {',1)
part=part.replace('\n\tif (until >= maxhpos) {','\n }\n\tif (until >= maxhpos) {',1)
s=s[:a]+part+s[z:]
for name,stage in [('STATIC_INLINE void beginning_of_plane_block_x (int hpos, int fm)',4),('STATIC_INLINE int flush_plane_data (int fm)',5)]:
 a=s.index(name+'\n{')+len(name+'\n{');s=s[:a]+f'\n GpScope inner({stage},gp_active);'+s[a:]
f.write_text(s);(record/'profile.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='reference/custom.cpp',tofile='profile/custom.cpp')))
for unit in ['custom','blitter','audio','disk','drawing']:
 subprocess.run([*b.RUN,'arm-none-eabi-g++',*c['flags'],'-c',b.inside(out/'src'/(unit+'.cpp')),'-o',b.inside(out/(unit+'.o'))],check=True)
sys.argv=['build_uae4arm_machine.py','--guest-jit','--hardware'];runpy.run_path('scripts/build_uae4arm_machine.py',run_name='__main__')
sys.argv=['lock-input.py',variant];runpy.run_path(str(p.parent/'sprite-decisions/lock-input.py'),run_name='__main__')
