from pathlib import Path
import subprocess
p=Path('.context/amiga/uae4arm/a1200/bitplane-spans');src=p.parent/'gameplay/build-pixel4/src';s=(src/'custom.cpp').read_text();h=(src/'include/custom.h').read_text()
def function(text,name):
 a=text.index(name);start=text.index('{',a);depth=1;z=start+1
 while depth:
  depth+=(text[z]=='{')-(text[z]=='}');z+=1
 return text[a:z]
block=function(s,'STATIC_INLINE void beginning_of_plane_block_x')
new=block.replace('beginning_of_plane_block_x','candidate').replace('compute_toscr_delay (hpos, bplcon1)', 'compute_toscr_delay_1 (bplcon1)').replace('compute_toscr_delay (hpos, bplcon1t)', 'compute_toscr_delay_1 (bplcon1t)')
fields=['bplcon0d','bplcon0dd','bplcon0_res','bplcon0_planes','toscr_res','toscr_res2p','toscr_nr_planes','toscr_nr_planes2','bpl_hstart','fetchstart_mask','fetchmode_size','fetchmode_mask','bplcon1','bplcon1_hpos']
head='''#include <cstdint>
#include <cstdio>
#include <cstring>
#define STATIC_INLINE static inline
using uae_u16=uint16_t;using uae_u32=uint32_t;
#define RES_LORES 0
#define RES_HIRES 1
#define RES_SUPERHIRES 2
#define RES_MAX 2
#define MAX_PLANES 8
#define HARD_DDF_START_REAL 0x18
#define CSMASK_ECS_DENISE 2
struct State {
'''+''.join(' int '+f+';\n' for f in fields)+''' int toscr_delay[2];
 uae_u32 todisplay[8][4],fetched[8],fetched_aga0[8],fetched_aga1[8];
 bool aga_mode;
 struct {int chipset_mask;} currprefs;
 struct {int plfleft;} thisline_decision;
 int events[16],nevents;
} st;
static unsigned updates;
'''
for f in fields+['toscr_delay','todisplay','fetched','fetched_aga0','fetched_aga1','aga_mode','currprefs','thisline_decision']:head+=f'auto &{f}=st.{f};\n'
head+='''void record_color_change2(int p,int r,unsigned v){st.events[st.nevents++]=p;st.events[st.nevents++]=r;st.events[st.nevents++]=v;}
void flush_display(int fm){st.events[st.nevents++]=fm;}
void maybe_first_bpl1dat(int hpos){if(thisline_decision.plfleft<0)thisline_decision.plfleft=hpos;}
'''
for text,name in [(h,'STATIC_INLINE int GET_RES_DENISE'),(h,'STATIC_INLINE int GET_PLANES'),(s,'STATIC_INLINE int isocs7planes'),(s,'STATIC_INLINE void update_denise'),(s,'STATIC_INLINE void compute_toscr_delay_1'),(s,'STATIC_INLINE void compute_toscr_delay (')]:
 f=function(text,name)
 if 'void update_denise' in name:f=f.replace('{','{ ++updates;',1)
 head+=f+'\n'
head+=block.replace('beginning_of_plane_block_x','reference')+'\n'+new+'\n'
head+='''static uint32_t rng=0x2917bb13;
uint32_t rnd(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
int main(){
 for(int t=0;t<200000;t++){
  memset(&st,0,sizeof(st));
  bplcon0d=rnd()&65535;bplcon0dd=t%3?bplcon0d:int(rnd());
  bplcon0_res=rnd()%3;bplcon0_planes=rnd()%9;toscr_nr_planes2=rnd()%9;
  bpl_hstart=rnd()%228;int fm=rnd()%3;fetchmode_size=16<<fm;fetchmode_mask=fetchmode_size-1;fetchstart_mask=(8<<fm)-1;
  bplcon1=rnd()&65535;int hp=rnd()%228;bplcon1_hpos=t%2?hp:hp-1;
  aga_mode=rnd()&1;currprefs.chipset_mask=(rnd()&1)*CSMASK_ECS_DENISE;thisline_decision.plfleft=t%3?-1:0;
  for(int i=0;i<8;i++){fetched[i]=rnd();fetched_aga0[i]=rnd();fetched_aga1[i]=rnd();for(int j=0;j<4;j++)todisplay[i][j]=rnd();}
  State initial=st;updates=0;reference(hp,fm);State expected=st;unsigned count=updates;
  st=initial;updates=0;candidate(hp,fm);
  if(memcmp(&expected,&st,sizeof(st))||count!=2||updates!=1){printf("FAIL %d\\n",t);return 1;}
 }
 puts("PASS 200000 block setup/state/colour-event comparisons; Denise updates 2 -> 1");
}
'''
(p/'denise-native.cpp').write_text(head)
subprocess.run(['clang++','-O2','-std=c++11','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'denise-native.cpp'),'-o',str(p/'denise-native')],check=True)
subprocess.run([str(p/'denise-native')],check=True)
