#include <cstdint>
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
 int bplcon0d;
 int bplcon0dd;
 int bplcon0_res;
 int bplcon0_planes;
 int toscr_res;
 int toscr_res2p;
 int toscr_nr_planes;
 int toscr_nr_planes2;
 int bpl_hstart;
 int fetchstart_mask;
 int fetchmode_size;
 int fetchmode_mask;
 int bplcon1;
 int bplcon1_hpos;
 int toscr_delay[2];
 uae_u32 todisplay[8][4],fetched[8],fetched_aga0[8],fetched_aga1[8];
 bool aga_mode;
 struct {int chipset_mask;} currprefs;
 struct {int plfleft;} thisline_decision;
 int events[16],nevents;
} st;
static unsigned updates;
auto &bplcon0d=st.bplcon0d;
auto &bplcon0dd=st.bplcon0dd;
auto &bplcon0_res=st.bplcon0_res;
auto &bplcon0_planes=st.bplcon0_planes;
auto &toscr_res=st.toscr_res;
auto &toscr_res2p=st.toscr_res2p;
auto &toscr_nr_planes=st.toscr_nr_planes;
auto &toscr_nr_planes2=st.toscr_nr_planes2;
auto &bpl_hstart=st.bpl_hstart;
auto &fetchstart_mask=st.fetchstart_mask;
auto &fetchmode_size=st.fetchmode_size;
auto &fetchmode_mask=st.fetchmode_mask;
auto &bplcon1=st.bplcon1;
auto &bplcon1_hpos=st.bplcon1_hpos;
auto &toscr_delay=st.toscr_delay;
auto &todisplay=st.todisplay;
auto &fetched=st.fetched;
auto &fetched_aga0=st.fetched_aga0;
auto &fetched_aga1=st.fetched_aga1;
auto &aga_mode=st.aga_mode;
auto &currprefs=st.currprefs;
auto &thisline_decision=st.thisline_decision;
void record_color_change2(int p,int r,unsigned v){st.events[st.nevents++]=p;st.events[st.nevents++]=r;st.events[st.nevents++]=v;}
void flush_display(int fm){st.events[st.nevents++]=fm;}
void maybe_first_bpl1dat(int hpos){if(thisline_decision.plfleft<0)thisline_decision.plfleft=hpos;}
STATIC_INLINE int GET_RES_DENISE (uae_u16 con0)
{
	if ((currprefs.chipset_mask & CSMASK_ECS_DENISE) && ((con0) & 0x40))
		return RES_SUPERHIRES; // SUPERHIRES
  return ((con0) & 0x8000) ? RES_HIRES : RES_LORES;
}
STATIC_INLINE int GET_PLANES(uae_u16 bplcon0)
{
  if ((bplcon0 & 0x0010) && (bplcon0 & 0x7000))
  	return 0; // >8 planes = 0 planes
  if (bplcon0 & 0x0010)
  	return 8; // AGA 8-planes bit
  return (bplcon0 >> 12) & 7; // normal planes bits
}
STATIC_INLINE int isocs7planes (void)
{
	return !(aga_mode) && bplcon0_res == 0 && bplcon0_planes == 7;
}
STATIC_INLINE void update_denise (int hpos)
{ ++updates;
	toscr_res = GET_RES_DENISE (bplcon0d);
  toscr_res2p = 2 << toscr_res;
	if (bplcon0dd != bplcon0d) {
		record_color_change2 (hpos, 0x100 + 0x1000, bplcon0d);
		bplcon0dd = bplcon0d;
	}
	toscr_nr_planes = GET_PLANES (bplcon0d);
	if (isocs7planes ()) {
		if (toscr_nr_planes2 < 6)
			toscr_nr_planes2 = 6;
	} else {
		toscr_nr_planes2 = toscr_nr_planes;
	}
}
STATIC_INLINE void compute_toscr_delay_1 (int bplcon1)
{
  int delay1 = (bplcon1 & 0x0f) | ((bplcon1 & 0x0c00) >> 6);
  int delay2 = ((bplcon1 >> 4) & 0x0f) | (((bplcon1 >> 4) & 0x0c00) >> 6);
  int shdelay1 = (bplcon1 >> 8) & 3;
  int shdelay2 = (bplcon1 >> 12) & 3;
	int delaymask = fetchmode_mask >> toscr_res;
    
	/* SPEEDUP code still needs this hack */
	int	delayoffset = fetchmode_size - (((bpl_hstart - HARD_DDF_START_REAL) & fetchstart_mask) << 1);
  delay1 += delayoffset;
  delay2 += delayoffset;
  toscr_delay[0] = (delay1 & delaymask) << toscr_res;
  toscr_delay[0] |= shdelay1 >> (RES_MAX - toscr_res);
  toscr_delay[1] = (delay2 & delaymask) << toscr_res;
  toscr_delay[1] |= shdelay2 >> (RES_MAX - toscr_res);
}
STATIC_INLINE void compute_toscr_delay (int hpos, int bplcon1)
{
	update_denise (hpos);
	compute_toscr_delay_1 (bplcon1);
}
STATIC_INLINE void reference (int hpos, int fm)
{
	int i;
	int oleft = thisline_decision.plfleft;
	static uae_u16 bplcon1t;

  flush_display (fm);

	if (fm == 0)
		for (i = 0; i < MAX_PLANES; i++) {
			todisplay[i][0] |= fetched[i];
  }
	else
		for (i = 0; i < MAX_PLANES; i++) {
			if (fm == 2)
				todisplay[i][1] = fetched_aga1[i];
			todisplay[i][0] = fetched_aga0[i];
	}

  maybe_first_bpl1dat (hpos);
	update_denise (hpos);

	// writing to BPLCON1 1 cycle after BPL1DAT access will
	// not (except first BPL1DAT write) affect the display
	// until next display block
	if (bplcon1_hpos != hpos || oleft < 0)
    compute_toscr_delay (hpos, bplcon1);
  else
    compute_toscr_delay (hpos, bplcon1t);
  bplcon1t = bplcon1;
}
STATIC_INLINE void candidate (int hpos, int fm)
{
	int i;
	int oleft = thisline_decision.plfleft;
	static uae_u16 bplcon1t;

  flush_display (fm);

	if (fm == 0)
		for (i = 0; i < MAX_PLANES; i++) {
			todisplay[i][0] |= fetched[i];
  }
	else
		for (i = 0; i < MAX_PLANES; i++) {
			if (fm == 2)
				todisplay[i][1] = fetched_aga1[i];
			todisplay[i][0] = fetched_aga0[i];
	}

  maybe_first_bpl1dat (hpos);
	update_denise (hpos);

	// writing to BPLCON1 1 cycle after BPL1DAT access will
	// not (except first BPL1DAT write) affect the display
	// until next display block
	if (bplcon1_hpos != hpos || oleft < 0)
    compute_toscr_delay_1 (bplcon1);
  else
    compute_toscr_delay_1 (bplcon1t);
  bplcon1t = bplcon1;
}
static uint32_t rng=0x2917bb13;
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
  if(memcmp(&expected,&st,sizeof(st))||count!=2||updates!=1){printf("FAIL %d\n",t);return 1;}
 }
 puts("PASS 200000 block setup/state/colour-event comparisons; Denise updates 2 -> 1");
}
