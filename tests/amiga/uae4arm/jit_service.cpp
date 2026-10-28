#include <cassert>
#include <cstdint>
#include <type_traits>
#include <csetjmp>
static uint32_t now,reads;
static inline uint32_t zzuae_jit_profile_clock(){++reads;return now;}
#include "jit_profile.h"
static_assert(std::is_trivially_destructible<ZuJitInterval>::value,"guest longjmp must not bypass a destructor");
int main(){
 ZuJitProfile p={1};
 {ZuJitInterval inactive(p,false,ZJ_STOP);now=7;inactive.finish();}
 assert(reads==0 && p.calls[ZJ_STOP]==0);
 now=0xfffffff0;
 {ZuJitInterval stop(p,true,ZJ_STOP);
  now=0;
  {ZuJitInterval copper(p,true,ZJ_COPPER);now=10;copper.finish();}
  now=32;stop.finish();
 }
 assert(p.ticks[ZJ_STOP]==48 && p.calls[ZJ_STOP]==1);
 assert(p.ticks[ZJ_COPPER]==10 && p.calls[ZJ_COPPER]==1);
 assert(p.ticks[ZJ_EVENTS]==0); // nested timers do not alter the outer bucket
 p.ticks[ZJ_STOP]=0xffffffffull;now=0;
 {ZuJitInterval stop(p,true,ZJ_STOP);now=1;stop.finish();}
 assert(p.ticks[ZJ_STOP]==0x100000000ull);
 std::jmp_buf escape;
 if(!setjmp(escape)){ZuJitInterval abandoned(p,true,ZJ_COPPER);now=99;longjmp(escape,1);}
 assert(p.ticks[ZJ_COPPER]==10 && p.calls[ZJ_COPPER]==1);

}
