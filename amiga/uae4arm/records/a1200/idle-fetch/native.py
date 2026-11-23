from pathlib import Path
p=Path(__file__).resolve().parent
s=Path('.context/amiga/uae4arm/a1200/gameplay/build-pixel4/src/custom.cpp').read_text()
a=s.index('STATIC_INLINE int one_fetch_cycle_0');z=s.index('static int one_fetch_cycle_fm0',a)
step=s[a:z]
head=r'''#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cassert>
#include <vector>
#define STATIC_INLINE static inline
#define _T(x) x
static void uae_abort(const char*,...){abort();}
enum {plf_idle,plf_start,plf_active,plf_wait_stop,plf_passed_stop,plf_passed_stop2,plf_end,plf_finished};
enum {fetch_not_started,fetch_started,fetch_was_plane0};
struct State {int plf_state,fetch_state,fetch_cycle,fetchunit_mask,fetchstart_mask,fm_maxplane,bpldmasetuphpos,toscr_nbits,toscr_res2p,line_cyclebased,badmode,fetchunit,fetchstart;bool bpl1dat_written;};
static State state;
'''
fields='plf_state fetch_state fetch_cycle fetchunit_mask fetchstart_mask fm_maxplane bpldmasetuphpos toscr_nbits toscr_res2p line_cyclebased badmode fetchunit fetchstart bpl1dat_written'.split()
head+=''.join('#define '+k+' state.'+k+'\n' for k in fields)
head+=r'''
static std::vector<uint64_t> events;
static void flush_display(int fm){events.push_back(0x100000000ull+fetch_cycle*32+toscr_nbits);toscr_nbits=0;}
static void finish_last_fetch(int pos,int fm){events.push_back(0x200000000ull+pos);plf_state=plf_end;}
static void maybe_check(int pos){if(bpldmasetuphpos>0&&pos>=bpldmasetuphpos){events.push_back(0x300000000ull+pos);bpldmasetuphpos=-1;}}
static void fetch(int nr,int fm){events.push_back(0x400000000ull+fetch_cycle*16+nr);if(!nr)bpl1dat_written=true;}
'''
body=r'''
static void run(int pos,int until,int stop,int dma,int fm,bool batch){
 for(;pos<until;pos++){
  int n=batch?zz_idle_span(pos,until,stop,dma,fm):0;
  if(n){fetch_cycle+=n;toscr_nbits+=n*toscr_res2p;if(toscr_nbits==16)flush_display(fm);pos+=n-1;continue;}
  if(fetch_state==fetch_was_plane0)events.push_back(0x500000000ull+pos);
  fetch_state=fetch_started;
  if(one_fetch_cycle_0(pos,stop,dma,fm))return;
 }
}
static uint32_t seed=0x12345678;
static uint32_t rnd(){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
int main(){unsigned eligible=0;
 for(unsigned i=0;i<1000000;i++){
  int unit=8<<(rnd()%3),res=2<<(rnd()%3),pos=rnd()%220,until=pos+rnd()%45,stop=pos-4+rnd()%45;
  state={int(rnd()%8),int(rnd()%3),int(rnd()%256),unit-1,unit-1,8,int(rnd()%5==0?pos+(rnd()%10):0),int(rnd()%(16/res))*res,res,int(rnd()%8==0),int(rnd()%16==0),unit,unit,bool(rnd()%8==0)};
  int dma=rnd()%4!=0,fm=rnd()%4?2:rnd()%2;
  if(zz_idle_span(pos,until,stop,dma,fm))eligible++;
  State initial=state;events.clear();run(pos,until,stop,dma,fm,false);State expected=state;auto trace=events;
  state=initial;events.clear();run(pos,until,stop,dma,fm,true);
  assert(events==trace);
'''
body+=''.join('  assert(state.'+k+'==expected.'+k+');\n' for k in [])
# Macros make field access awkward; compare fields through local scalar captures.
body+='  assert(same(state,expected));\n }\n printf("PASS 1000000 cycle/event comparisons, %u initial eligible spans\\n",eligible);\n}\n'
compare=''.join('#undef '+k+'\n' for k in fields)
compare+='static bool same(const State&a,const State&b){return '+ '&&'.join('a.'+k+'==b.'+k for k in fields)+';}\n'
body=body.replace('static uint32_t seed=',compare+'static uint32_t seed=')
(p/'native.cpp').write_text(head+step+(p/'idle_span.inc').read_text()+body)
