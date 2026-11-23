#include <cstdint>
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
#define plf_state state.plf_state
#define fetch_state state.fetch_state
#define fetch_cycle state.fetch_cycle
#define fetchunit_mask state.fetchunit_mask
#define fetchstart_mask state.fetchstart_mask
#define fm_maxplane state.fm_maxplane
#define bpldmasetuphpos state.bpldmasetuphpos
#define toscr_nbits state.toscr_nbits
#define toscr_res2p state.toscr_res2p
#define line_cyclebased state.line_cyclebased
#define badmode state.badmode
#define fetchunit state.fetchunit
#define fetchstart state.fetchstart
#define bpl1dat_written state.bpl1dat_written

static std::vector<uint64_t> events;
static void flush_display(int fm){events.push_back(0x100000000ull+fetch_cycle*32+toscr_nbits);toscr_nbits=0;}
static void finish_last_fetch(int pos,int fm){events.push_back(0x200000000ull+pos);plf_state=plf_end;}
static void maybe_check(int pos){if(bpldmasetuphpos>0&&pos>=bpldmasetuphpos){events.push_back(0x300000000ull+pos);bpldmasetuphpos=-1;}}
static void fetch(int nr,int fm){events.push_back(0x400000000ull+fetch_cycle*16+nr);if(!nr)bpl1dat_written=true;}
STATIC_INLINE int one_fetch_cycle_0 (int pos, int ddfstop_to_test, int dma, int fm)
{
	if (plf_state < plf_passed_stop && pos == ddfstop_to_test)
		plf_state = plf_passed_stop;

	if ((fetch_cycle & fetchunit_mask) == 0) {
		if (plf_state == plf_passed_stop2) {
			finish_last_fetch (pos, fm);
			return 1;
		}
		if (plf_state == plf_passed_stop) {
			plf_state = plf_passed_stop2;
		} else if (plf_state == plf_passed_stop2) {
			plf_state = plf_end;
    }
	}

	maybe_check (pos);

	if (dma && plf_state != plf_wait_stop) {
	  /* fetchstart_mask can be larger than fm_maxplane if FMODE > 0.  This means
	   that the remaining cycles are idle; we'll fall through the whole switch
	   without doing anything.  */
		int cycle_start = fetch_cycle & fetchstart_mask;
		switch (fm_maxplane) {
			case 8:
				switch (cycle_start) {
					case 0: fetch (7, fm); break;
					case 1: fetch (3, fm); break;
					case 2: fetch (5, fm); break;
					case 3: fetch (1, fm); break;
					case 4: fetch (6, fm); break;
					case 5: fetch (2, fm); break;
					case 6: fetch (4, fm); break;
					case 7: fetch (0, fm); break;
				}
				break;
			case 4:
				switch (cycle_start) {
					case 0: fetch (3, fm); break;
					case 1: fetch (1, fm); break;
					case 2: fetch (2, fm); break;
					case 3: fetch (0, fm); break;
				}
				break;
			case 2:
				switch (cycle_start) {
					case 0: fetch (1, fm); break;
					case 1: fetch (0, fm); break;
				}
				break;
		}
	}

	if (bpl1dat_written) {
		// do this here because if program plays with BPLCON0 during scanline
		// it is possible that one DMA BPL1DAT write is completely missed
		// and we must not draw anything at all in next dma block if this happens
		// (Disposable Hero titlescreen)
		fetch_state = fetch_was_plane0;
		bpl1dat_written = false;
	}

	fetch_cycle++;
	toscr_nbits += toscr_res2p;

	if (toscr_nbits > 16) {
		uae_abort (_T("toscr_nbits > 16 (%d)"), toscr_nbits);
		toscr_nbits = 0;
	}
	if (toscr_nbits == 16)
		flush_display (fm);
	
	return 0;
}

/* Only idle AGA fetch phases. Stop before any state-changing boundary. */
STATIC_INLINE int zz_idle_span(int pos, int until, int stop, int dma, int fm)
{
    if (fm != 2 || !dma || line_cyclebased || badmode || bpldmasetuphpos > 0 ||
        bpl1dat_written || fetch_state != fetch_started || (plf_state < plf_active || plf_state > plf_passed_stop2))
        return 0;
    int phase = fetch_cycle & fetchstart_mask;
    if (phase < fm_maxplane || toscr_nbits < 0 || toscr_nbits >= 16 ||
        (toscr_res2p != 2 && toscr_res2p != 4 && toscr_res2p != 8) ||
        ((16 - toscr_nbits) & (toscr_res2p - 1)))
        return 0;
    int count = fetchstart - phase;
    if (count > until - pos) count = until - pos;
    if (plf_state < plf_passed_stop && count > stop - pos) count = stop - pos;
    int unit = fetchunit - (fetch_cycle & fetchunit_mask);
    if (count > unit) count = unit;
    int flush = (16 - toscr_nbits) >> __builtin_ctz((unsigned)toscr_res2p);
    if (count > flush) count = flush;
    return count >= 2 ? count : 0;
}

static void run(int pos,int until,int stop,int dma,int fm,bool batch){
 for(;pos<until;pos++){
  int n=batch?zz_idle_span(pos,until,stop,dma,fm):0;
  if(n){fetch_cycle+=n;toscr_nbits+=n*toscr_res2p;if(toscr_nbits==16)flush_display(fm);pos+=n-1;continue;}
  if(fetch_state==fetch_was_plane0)events.push_back(0x500000000ull+pos);
  fetch_state=fetch_started;
  if(one_fetch_cycle_0(pos,stop,dma,fm))return;
 }
}
#undef plf_state
#undef fetch_state
#undef fetch_cycle
#undef fetchunit_mask
#undef fetchstart_mask
#undef fm_maxplane
#undef bpldmasetuphpos
#undef toscr_nbits
#undef toscr_res2p
#undef line_cyclebased
#undef badmode
#undef fetchunit
#undef fetchstart
#undef bpl1dat_written
static bool same(const State&a,const State&b){return a.plf_state==b.plf_state&&a.fetch_state==b.fetch_state&&a.fetch_cycle==b.fetch_cycle&&a.fetchunit_mask==b.fetchunit_mask&&a.fetchstart_mask==b.fetchstart_mask&&a.fm_maxplane==b.fm_maxplane&&a.bpldmasetuphpos==b.bpldmasetuphpos&&a.toscr_nbits==b.toscr_nbits&&a.toscr_res2p==b.toscr_res2p&&a.line_cyclebased==b.line_cyclebased&&a.badmode==b.badmode&&a.fetchunit==b.fetchunit&&a.fetchstart==b.fetchstart&&a.bpl1dat_written==b.bpl1dat_written;}
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
  assert(same(state,expected));
 }
 printf("PASS 1000000 cycle/event comparisons, %u initial eligible spans\n",eligible);
}
