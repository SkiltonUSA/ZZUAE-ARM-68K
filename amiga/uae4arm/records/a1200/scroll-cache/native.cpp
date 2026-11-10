#include <cassert>
#include <cstdio>
#include <random>
#define STATIC_INLINE static inline
#define HARD_DDF_START_REAL 0x18
#define RES_MAX 2
int fetchmode_mask,fetchmode_size,fetchstart_mask,bpl_hstart,toscr_res,toscr_delay[2];
STATIC_INLINE void reference (int bplcon1)
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

STATIC_INLINE void compute_toscr_delay_1 (int bplcon1)
{
  // Exact dependency cache: no DMA, Copper or Denise update is skipped.
  struct DelayPlan {
    int con1, mask, size, start_mask, hstart, res, delay[2];
    bool valid;
  };
  static DelayPlan plan;
  if (plan.valid && plan.con1 == bplcon1 && plan.mask == fetchmode_mask
      && plan.size == fetchmode_size && plan.start_mask == fetchstart_mask
      && plan.hstart == bpl_hstart && plan.res == toscr_res) {
    toscr_delay[0] = plan.delay[0];
    toscr_delay[1] = plan.delay[1];
    return;
  }

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
  plan.con1 = bplcon1;
  plan.mask = fetchmode_mask;
  plan.size = fetchmode_size;
  plan.start_mask = fetchstart_mask;
  plan.hstart = bpl_hstart;
  plan.res = toscr_res;
  plan.delay[0] = toscr_delay[0];
  plan.delay[1] = toscr_delay[1];
  plan.valid = true;
}


unsigned tests;
void check(int con) {
 reference(con); int a=toscr_delay[0],b=toscr_delay[1];
 for(int repeat=0;repeat<3;repeat++){
  toscr_delay[0]=toscr_delay[1]=-1;
  compute_toscr_delay_1(con);
  assert(toscr_delay[0]==a && toscr_delay[1]==b);tests++;
 }
}
int main(){
 std::mt19937 rng(1200);
 for(unsigned n=0;n<100000;n++){
  int con=n<65536?n:rng()&65535;
  fetchmode_size=16<<(rng()%3); fetchmode_mask=fetchmode_size-1;
  fetchstart_mask=(1<<(1+rng()%5))-1; bpl_hstart=int(rng()%300)-20;
  for(int r=0;r<3;r++){
   toscr_res=r;check(con);check(con^0x1234);check(con);
   int* fields[]={&fetchmode_mask,&fetchmode_size,&fetchstart_mask,&bpl_hstart,&toscr_res};
   int values[]={fetchmode_mask^16,fetchmode_size^32,fetchstart_mask^8,bpl_hstart+1,(r+1)%3};
   for(int i=0;i<5;i++){int old=*fields[i];*fields[i]=values[i];check(con);*fields[i]=old;check(con);}
  }
 }
 printf("PASS %u exact comparisons: all BPLCON1 values, repeated calls, each dependency mutated alone\n",tests);
}
