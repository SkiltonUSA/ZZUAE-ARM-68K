#include <cassert>
#include <cstdint>
#include <cstring>
static uint32_t clock_value,clock_reads;
static inline uint32_t zzuae_jit_profile_clock(){++clock_reads;return clock_value;}
#include "jit_profile.h"
int main(){
 ZuJitProfile p={1};unsigned selected=0;
 for(unsigned i=0;i<100000;i++)selected+=p.choose();
 assert(p.dispatches==100000 && selected==p.samples);
 assert(selected>200 && selected<600);
 ZuJitProfile measured={1};
 for(unsigned n=0;n<10000;n++){
  clock_value=0xfffffff0u;unsigned before=clock_reads;
  ZuJitSample sample(measured);
  if(!sample.active){sample.mark(ZJ_VALIDATION);assert(clock_reads==before);continue;}
  assert(clock_reads==before+1);
  clock_value=0x10;sample.mark(ZJ_VALIDATION);
  clock_value=0x30;sample.mark(ZJ_HANDLER);
  assert(measured.ticks[ZJ_VALIDATION]==32 && measured.calls[ZJ_VALIDATION]==1);
  assert(measured.ticks[ZJ_HANDLER]==32 && measured.calls[ZJ_HANDLER]==1);
  measured.ticks[ZJ_HANDLER]=0xffffffffu;
  clock_value=0x31;sample.mark(ZJ_HANDLER);
  assert(measured.ticks[ZJ_HANDLER]==0x100000000ull);
  unsigned char wire[ZJ_PROFILE_BYTES+8];memset(wire,0xa5,sizeof wire);
  measured.publish(wire+4);
  assert(ad_get(wire+4,0)==ZJ_PROFILE_MAGIC);
  assert(ad_get(wire+4,4)==measured.dispatches && ad_get(wire+4,8)==1);
  assert(ad_get(wire+4,16+16*ZJ_HANDLER)==1);
  assert(ad_get(wire+4,20+16*ZJ_HANDLER)==0);
  assert(ad_get(wire+4,24+16*ZJ_HANDLER)==2);
  for(unsigned i=0;i<4;i++)assert(wire[i]==0xa5 && wire[ZJ_PROFILE_BYTES+4+i]==0xa5);
  return 0;
 }
 assert(false && "sampler never selected a dispatch");
}
