// Comparison fixture: pinned UAE do_cycles_cpu_fastest vs candidate shortcut.
// Upstream event code: UAE, Bernd Schmidt, Alessandro Bissacco and Toni Wilen.
#include <cstdint>
#include <cassert>
#include <cstdio>
using uae_u32=uint32_t;
struct {int pissoff;} regs;
uint32_t currcycle,nextevent; int is_syncline,vsyncmintime,vsynctimebase=20000,speedup_timelimit=10,pissoff_value=100;
int stamp; int read_processor_time(){return stamp;}
unsigned calls,other_calls; const int ev_max=1;
struct Event {bool active; uint32_t evtime; void(*handler)();} eventtab[1];
void handler(){++calls;eventtab[0].evtime+=257;}
void events_schedule(){nextevent=eventtab[0].evtime;}
void do_cycles_cpu_fastest (uae_u32 cycles_to_add)
{
  if ((regs.pissoff -= cycles_to_add) > 0)
  	return;

  cycles_to_add = -regs.pissoff;
  regs.pissoff = 0;

	/* Keep only CPU emulation running while waiting for sync point. */
  if (is_syncline) {
	  int rpt = read_processor_time ();
	  int v = rpt - vsyncmintime;
	  if (v > vsynctimebase || v < -vsynctimebase) {
	    v = 0;
    }
  	if (v < speedup_timelimit) {
	    regs.pissoff = pissoff_value;
	    return;
  	}
  	is_syncline = 0;
  }

  while ((nextevent - currcycle) <= cycles_to_add) {
	  int i;

	  cycles_to_add -= (nextevent - currcycle);
	  currcycle = nextevent;

  	for (i = 0; i < ev_max; i++) {
	    if (eventtab[i].active && eventtab[i].evtime == currcycle) {
    		(*eventtab[i].handler)();
	    }
  	}
  	events_schedule();
  }
  currcycle += cycles_to_add;
}

void other(uae_u32 n){++other_calls;currcycle+=n;}
void(*do_cycles)(uae_u32);
static inline void zzuae_advance_cycles(uae_u32 cycles) {
 if(do_cycles==do_cycles_cpu_fastest && regs.pissoff==0 && !is_syncline &&
    cycles<(nextevent-currcycle)) {currcycle+=cycles;return;}
 do_cycles(cycles);
}
struct State {int budget,sync;uint32_t cycle,next,event;unsigned calls,other;};
State state(){return {regs.pissoff,is_syncline,currcycle,nextevent,eventtab[0].evtime,calls,other_calls};}
void restore(State s){regs.pissoff=s.budget;is_syncline=s.sync;currcycle=s.cycle;nextevent=s.next;eventtab[0]={true,s.event,handler};calls=s.calls;other_calls=s.other;}
bool equal(State a,State b){return a.budget==b.budget && a.sync==b.sync && a.cycle==b.cycle && a.next==b.next && a.event==b.event && a.calls==b.calls && a.other==b.other;}
uint32_t rng=0x78219abc;uint32_t random32(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
int main(){
 for(unsigned i=0;i<100000;i++){
  uint32_t c=random32(),delta=random32()%500,cycles=i%4==0?delta:random32()%1000;
  State initial={i%3==0?0:int(random32()%200)-100,int(i%5==0),c,c+delta,c+delta,0,0};
  stamp=int(random32()%40000)-20000;vsyncmintime=0;
  do_cycles=i%7==0?other:do_cycles_cpu_fastest;
  restore(initial);do_cycles(cycles);State expected=state();
  restore(initial);zzuae_advance_cycles(cycles);assert(equal(expected,state()));
 }
 puts("PASS 100000 event-boundary, wraparound, budget, sync and alternate-handler cases");
}
