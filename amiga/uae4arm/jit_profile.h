#pragma once
#include <stdint.h>
#include "../arm_debug/protocol.h"
#define ZJ_PROFILE_BASE 0x482980u
#define ZJ_PROFILE_MAGIC 0x4a505246u
/* Five non-overlapping sampled intervals. Handler includes cold learning and
 * guest-cycle/event callbacks; event service can also occur inside fallback. */
enum {ZJ_DISPATCH,ZJ_VALIDATION,ZJ_HANDLER,ZJ_INTERPRETER,ZJ_EVENTS,ZJ_STAGES};
#define ZJ_PROFILE_BYTES (16u+16u*ZJ_STAGES)
#ifdef __cplusplus
static_assert(ZJ_PROFILE_BASE+ZJ_PROFILE_BYTES<=0x482a00u,"profile overlaps cache report");
struct ZuJitProfile {
 uint32_t rng,dispatches,samples;
 uint64_t ticks[ZJ_STAGES];uint32_t calls[ZJ_STAGES];
 bool choose(){
  ++dispatches;rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
  bool chosen=(rng&255u)==0;if(chosen)++samples;return chosen;
 }
 void publish(volatile uint8_t *wire)const{
  ad_put(wire,0,ZJ_PROFILE_MAGIC);ad_put(wire,4,dispatches);ad_put(wire,8,samples);
  for(unsigned i=0;i<ZJ_STAGES;i++){
   ad_put(wire,16+16*i,(uint32_t)(ticks[i]>>32));
   ad_put(wire,20+16*i,(uint32_t)ticks[i]);ad_put(wire,24+16*i,calls[i]);
  }
 }
};
/* Defined by the payload; native tests supply a deterministic clock. */
static inline uint32_t zzuae_jit_profile_clock();
struct ZuJitSample {
 ZuJitProfile &profile;bool active;uint32_t last;
 explicit ZuJitSample(ZuJitProfile &p):profile(p),active(p.choose()),last(active?zzuae_jit_profile_clock():0){}
 void mark(unsigned stage){
  if(active){
   uint32_t now=zzuae_jit_profile_clock();
   profile.ticks[stage]+=(uint32_t)(now-last);++profile.calls[stage];
   // Exclude counter accumulation from the following interval. Clock reads
   // still have a cost; sampled times are diagnostic, not cycle-accurate.
   last=zzuae_jit_profile_clock();
  }
 }
};
#endif
