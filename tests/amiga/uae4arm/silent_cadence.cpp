#include <cassert>
#include <cstdio>
#include <initializer_list>
#include "../../../amiga/uae4arm/display_clock.h"
#include "../../../amiga/uae4arm/render_cadence.inc"
int main(){
 for(unsigned hz:{50u,60u})for(unsigned rate:{25u,30u,50u,60u,0u})for(int audio:{0,1}){
  unsigned requested=rate?(1000000u+rate-1)/rate:0;
  auto c=zu_display_clock_plan(requested,audio,hz);
  unsigned phase=0,draws=0;
  for(unsigned n=0;n<6000;n++)draws+=zu_render_due(c.rate,phase,hz);
  unsigned expected=rate&&rate<hz?6000*rate/hz:6000;
  assert(draws==expected);
  if(audio||!rate)assert(c.period==0);
  else {
   // Over a long run, lower display rates must not slow the guest clock.
   uint64_t elapsed=uint64_t(draws)*c.period,guest=6000000000ull/hz;
   assert(elapsed>=guest&&elapsed-guest<6000);
  }
 }
 puts("PASS silent display cadence: PAL/NTSC, 25/30/50/60/MAX, sound on/off, guest-time preservation and over-rate clamp");
}
