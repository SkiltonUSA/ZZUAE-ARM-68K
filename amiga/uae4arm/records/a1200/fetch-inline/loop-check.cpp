#include <cassert>
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
int dma;
int drawing;
int plf_state;
int ddfstop;
int last_fetch_hpos;
int plfstop;
int fetch_cycle;
int cycle_diagram_shift;
int fetch_state;
int diwstate;
int line_cyclebased;
int fetchstart_mask;
int fm_maxplane;
int badmode;
int toscr_nr_planes;
int fetchunit_mask;
int fetchunit;
int fetchstart;
int toscr_res;
int maxhpos;
int stop_at;
Line line;Prefs prefs;
} state;
int &dma=state.dma;
int &drawing=state.drawing;
int &plf_state=state.plf_state;
int &ddfstop=state.ddfstop;
int &last_fetch_hpos=state.last_fetch_hpos;
int &plfstop=state.plfstop;
int &fetch_cycle=state.fetch_cycle;
int &cycle_diagram_shift=state.cycle_diagram_shift;
int &fetch_state=state.fetch_state;
int &diwstate=state.diwstate;
int &line_cyclebased=state.line_cyclebased;
int &fetchstart_mask=state.fetchstart_mask;
int &fm_maxplane=state.fm_maxplane;
int &badmode=state.badmode;
int &toscr_nr_planes=state.toscr_nr_planes;
int &fetchunit_mask=state.fetchunit_mask;
int &fetchunit=state.fetchunit;
int &fetchstart=state.fetchstart;
int &toscr_res=state.toscr_res;
int &maxhpos=state.maxhpos;
int &stop_at=state.stop_at;
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
STATIC_INLINE void reference (int until, int fm)
{
	int pos;
	int dma = dmaen (DMA_BITPLANE);
	int ddfstop_to_test;

  if (nodraw() || plf_state >= plf_end)
		return;

  /* We need an explicit test against HARD_DDF_STOP here to guard against
     programs that move the DDFSTOP before our current position before we
     reach it.  */
	ddfstop_to_test = HARD_DDF_STOP;
	if (ddfstop >= last_fetch_hpos && plfstop < HARD_DDF_STOP)
		ddfstop_to_test = plfstop;

	update_toscr_planes();

	pos = last_fetch_hpos;
  cycle_diagram_shift = last_fetch_hpos - fetch_cycle;

	/* First, a loop that prepares us for the speedup code.  We want to enter
     the SPEEDUP case with fetch_state == fetch_was_plane0, and then unroll
     whole blocks, so that we end on the same fetch_state again.  */
	for (; ; pos++) {
		if (pos == until) {
			if (until >= maxhpos) {
				maybe_finish_last_fetch (pos, fm);
				return;
			}
			flush_display (fm);
			return;
		}

		if (fetch_state == fetch_was_plane0)
			break;
		fetch_start ();
		if (one_fetch_cycle (pos, ddfstop_to_test, dma, fm))
		  return;
	}

	// vdiw getting cleared mid-scan = fetches also stop
	if (diwstate == DIW_waiting_start && plf_state < plf_wait_stop) {
		// ecs = continue at passed_stop
		// ocs = line is done
		if (currprefs.chipset_mask & CSMASK_ECS_AGNUS)
			plf_state = plf_wait_stop;
		else
			plf_state = plf_passed_stop2;
	}

	/* Unrolled version of the for loop below.  */
	if (plf_state < plf_wait_stop && !line_cyclebased	&& dma
		&& (fetch_cycle & fetchstart_mask) == (fm_maxplane & fetchstart_mask)
		&& !badmode
		&& toscr_nr_planes == thisline_decision.nr_planes)
	{
		int offs = (pos - fetch_cycle) & fetchunit_mask;
		int ddf2 = ((ddfstop_to_test - offs + fetchunit - 1) & ~fetchunit_mask) + offs;
		int ddf3 = ddf2 + fetchunit;
		int stop = until < ddf2 ? until : until < ddf3 ? ddf2 : ddf3;
		int count;

		count = stop - pos;
		if (count >= fetchstart) {
			count &= ~fetchstart_mask;
			int stoppos = pos + count;

			if (thisline_decision.plfleft < 0) {
				compute_toscr_delay_1 (bplcon1);
			}
			do_long_fetch (count >> (3 - toscr_res), dma, fm);

	    /* This must come _after_ do_long_fetch so as not to confuse flush_display
	       into thinking the first fetch has produced any output worth emitting to
	       the screen.  But the calculation of delay_offset must happen _before_.  */
			maybe_first_bpl1dat (pos);

	    if (pos <= ddfstop_to_test && stoppos > ddfstop_to_test) {
				plf_state = plf_passed_stop;
      }
	    if (pos <= ddfstop_to_test && stoppos > ddf2) {
				plf_state = plf_passed_stop2;
      }
 	    if (pos <= ddf2 && stoppos >= ddf2 + fm_maxplane) {
			  add_modulos ();
      }
			pos += count;
			fetch_cycle += count;
		}
	}

	for (; pos < until; pos++) {
		if (fetch_state == fetch_was_plane0) {
			beginning_of_plane_block (pos, fm);
	    estimate_last_fetch_cycle (pos);
    }
		fetch_start ();

		if (one_fetch_cycle (pos, ddfstop_to_test, dma, fm))
		   return;
	}
	if (until >= maxhpos) {
		maybe_finish_last_fetch (pos, fm);
		return;
	}
	flush_display (fm);
}

STATIC_INLINE void candidate (int until, int fm)
{
	int pos;
	int dma = dmaen (DMA_BITPLANE);
	int ddfstop_to_test;

  if (nodraw() || plf_state >= plf_end)
		return;

  /* We need an explicit test against HARD_DDF_STOP here to guard against
     programs that move the DDFSTOP before our current position before we
     reach it.  */
	ddfstop_to_test = HARD_DDF_STOP;
	if (ddfstop >= last_fetch_hpos && plfstop < HARD_DDF_STOP)
		ddfstop_to_test = plfstop;

	update_toscr_planes();

	pos = last_fetch_hpos;
  cycle_diagram_shift = last_fetch_hpos - fetch_cycle;


    bool preparing = true;
    for (;;) {
        if (pos == until) {
            if (until >= maxhpos) {
                maybe_finish_last_fetch(pos, fm);
                return;
            }
            flush_display(fm);
            return;
        }
        if (preparing && fetch_state == fetch_was_plane0) {
	// vdiw getting cleared mid-scan = fetches also stop
	if (diwstate == DIW_waiting_start && plf_state < plf_wait_stop) {
		// ecs = continue at passed_stop
		// ocs = line is done
		if (currprefs.chipset_mask & CSMASK_ECS_AGNUS)
			plf_state = plf_wait_stop;
		else
			plf_state = plf_passed_stop2;
	}

	/* Unrolled version of the for loop below.  */
	if (plf_state < plf_wait_stop && !line_cyclebased	&& dma
		&& (fetch_cycle & fetchstart_mask) == (fm_maxplane & fetchstart_mask)
		&& !badmode
		&& toscr_nr_planes == thisline_decision.nr_planes)
	{
		int offs = (pos - fetch_cycle) & fetchunit_mask;
		int ddf2 = ((ddfstop_to_test - offs + fetchunit - 1) & ~fetchunit_mask) + offs;
		int ddf3 = ddf2 + fetchunit;
		int stop = until < ddf2 ? until : until < ddf3 ? ddf2 : ddf3;
		int count;

		count = stop - pos;
		if (count >= fetchstart) {
			count &= ~fetchstart_mask;
			int stoppos = pos + count;

			if (thisline_decision.plfleft < 0) {
				compute_toscr_delay_1 (bplcon1);
			}
			do_long_fetch (count >> (3 - toscr_res), dma, fm);

	    /* This must come _after_ do_long_fetch so as not to confuse flush_display
	       into thinking the first fetch has produced any output worth emitting to
	       the screen.  But the calculation of delay_offset must happen _before_.  */
			maybe_first_bpl1dat (pos);

	    if (pos <= ddfstop_to_test && stoppos > ddfstop_to_test) {
				plf_state = plf_passed_stop;
      }
	    if (pos <= ddfstop_to_test && stoppos > ddf2) {
				plf_state = plf_passed_stop2;
      }
 	    if (pos <= ddf2 && stoppos >= ddf2 + fm_maxplane) {
			  add_modulos ();
      }
			pos += count;
			fetch_cycle += count;
		}
	}


            preparing = false;
            continue;
        }
        if (!preparing && fetch_state == fetch_was_plane0) {
            beginning_of_plane_block(pos, fm);
            estimate_last_fetch_cycle(pos);
        }
        fetch_start();
        if (one_fetch_cycle_0(pos, ddfstop_to_test, dma, fm))
            return;
        ++pos;
    }
}


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
  if(std::memcmp(&state,&expected,sizeof(state)) || events!=trace){fprintf(stderr,"FAIL case %u\n",test);return 1;}
 }
 for(unsigned long n:counts)assert(n>100);
 printf("PASS 100000 source-loop state/callback traces; bulk calls %lu, per-cycle calls %lu\n",counts[7],counts[3]);
}
