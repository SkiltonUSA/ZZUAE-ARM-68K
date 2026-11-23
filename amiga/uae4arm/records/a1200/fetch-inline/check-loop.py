"""Compare real loop source with deterministic, stateful chipset callbacks.

This checks callback ordering/control flow; actual chipset semantics are checked
separately by the ARM fixtures and physical runs.
"""
from pathlib import Path
import subprocess

p = Path('.context/amiga/uae4arm/a1200/fetch-inline')
g = p.parent / 'gameplay'
fields = 'dma drawing plf_state ddfstop last_fetch_hpos plfstop fetch_cycle cycle_diagram_shift fetch_state diwstate line_cyclebased fetchstart_mask fm_maxplane badmode toscr_nr_planes fetchunit_mask fetchunit fetchstart toscr_res maxhpos stop_at'.split()
s = '''#include <cassert>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <vector>
#include <algorithm>
#define STATIC_INLINE static inline
enum {plf_idle,plf_start,plf_active,plf_wait_stop,plf_passed_stop,plf_passed_stop2,plf_end,plf_finished};
enum {fetch_not_started,fetch_started,fetch_was_plane0};
enum {DIW_waiting_start,DIW_waiting_stop};
enum {HARD_DDF_STOP=212,DMA_BITPLANE=1,CSMASK_ECS_AGNUS=2};
struct Line {int plfleft,nr_planes;};
struct Prefs {int chipset_mask;};
struct State {
''' + '\n'.join('int '+n+';' for n in fields) + '''
Line line;Prefs prefs;
} state;
''' + '\n'.join('int &'+n+'=state.'+n+';' for n in fields) + '''
Line &thisline_decision=state.line;
Prefs &currprefs=state.prefs;
std::vector<int> events;
unsigned long counts[9];
void event(int id,int a=0,int b=0,int c=0){
 assert(events.size()<10000);++counts[id];
 for(int v:{id,a,b,c,fetch_cycle,fetch_state,plf_state})events.push_back(v);
}
int nodraw(){return !drawing;}
int dmaen(int){return dma;}
void update_toscr_planes(){event(0);thisline_decision.nr_planes=std::max(thisline_decision.nr_planes,toscr_nr_planes);}
void maybe_finish_last_fetch(int pos,int fm){event(1,pos,fm);fetch_state=fetch_not_started;}
void flush_display(int fm){event(2,fm);}
void fetch_start(){fetch_state=fetch_started;}
int one_fetch_cycle_0(int pos,int stop,int enabled,int fm){
 event(3,pos,stop,enabled*4+fm);
 if(pos>=stop_at)return 1;
 ++fetch_cycle;
 fetch_state=(fetch_cycle&fetchstart_mask)?fetch_started:fetch_was_plane0;
 if(pos==stop)plf_state=plf_passed_stop;
 return 0;
}
int one_fetch_cycle(int a,int b,int c,int d){return one_fetch_cycle_0(a,b,c,d);}
void beginning_of_plane_block(int pos,int fm){event(4,pos,fm);}
void estimate_last_fetch_cycle(int pos){event(5,pos);}
void compute_toscr_delay_1(int v){event(6,v);}
int bplcon1=0x23;
void do_long_fetch(int count,int enabled,int fm){event(7,count,enabled,fm);fetch_state=fetch_was_plane0;}
void maybe_first_bpl1dat(int pos){event(8,pos);if(thisline_decision.plfleft<0)thisline_decision.plfleft=pos;}
void add_modulos(){event(8,-2);}
'''
for variant, name in [('pixel4', 'reference'), ('fetch-fused', 'candidate')]:
    src = (g / ('build-' + variant) / 'src/custom.cpp').read_text()
    a = src.index('STATIC_INLINE void update_fetch (int until, int fm)')
    z = src.index('static void update_fetch_0', a)
    s += src[a:z].replace('void update_fetch ', 'void ' + name + ' ', 1)
s += '''
uint32_t seed=0x692b4531;
unsigned random_value(){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
int main(){
 for(unsigned test=0;test<100000;++test){
  state={};drawing=(random_value()%8)!=0;dma=random_value()%2;
  plf_state=random_value()%8;fetch_state=random_value()%3;
  maxhpos=227;last_fetch_hpos=random_value()%228;
  int until=last_fetch_hpos+random_value()%(231-last_fetch_hpos);
  int fm=random_value()%3;toscr_res=random_value()%3;
  int starts[9]={3,2,1,4,3,2,5,4,3};int units[9]={8,8,8,16,8,8,32,16,8};int planes[9]={8,4,2,8,8,4,8,8,8};
  fetchstart=1<<starts[fm*3+toscr_res];fetchstart_mask=fetchstart-1;
  fetchunit=units[fm*3+toscr_res];fetchunit_mask=fetchunit-1;fm_maxplane=planes[fm*3+toscr_res];
  fetch_cycle=random_value()%512;ddfstop=(int)(random_value()%270)-20;plfstop=(int)(random_value()%270)-20;
  line_cyclebased=random_value()%4==0;badmode=random_value()%4==0;
  diwstate=random_value()%2;currprefs.chipset_mask=random_value()%2?CSMASK_ECS_AGNUS:0;
  toscr_nr_planes=random_value()%9;thisline_decision.nr_planes=random_value()%9;
  thisline_decision.plfleft=random_value()%2?-1:30;stop_at=random_value()%260;
  State initial=state;events.clear();reference(until,fm);State expected=state;auto trace=events;
  state=initial;events.clear();candidate(until,fm);
  if(std::memcmp(&state,&expected,sizeof(state)) || events!=trace){fprintf(stderr,"FAIL case %u\\n",test);return 1;}
 }
 for(unsigned long n:counts)assert(n>100);
 printf("PASS 100000 source-loop state/callback traces; bulk calls %lu, per-cycle calls %lu\\n",counts[7],counts[3]);
}
'''
(p / 'loop-check.cpp').write_text(s)
subprocess.run(['clang++', '-std=c++11', '-O2', '-fsanitize=address,undefined',
                str(p / 'loop-check.cpp'), '-o', str(p / 'loop-check')], check=True)
subprocess.run([str(p / 'loop-check')], check=True)
