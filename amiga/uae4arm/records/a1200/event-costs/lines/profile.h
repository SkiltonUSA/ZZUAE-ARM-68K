/* Optional diagnostic timers; never enabled in normal/release builds.
 * Inclusive stages overlap (drawing includes bitplanes AND presentation;
 * audio includes PCM publication; presentation includes conversion).
 * Do not sum their shares. Timers include waiting, not just busy CPU work. */
#pragma once
#include <stdint.h>
#define ZU_PROFILE_BASE 0x482900u
#define ZU_PROFILE_STAGES 8u
#ifdef ZZUAE_PROFILE
extern uint64_t zu_profile_ticks[ZU_PROFILE_STAGES];
extern uint32_t zu_profile_calls[ZU_PROFILE_STAGES];
static inline uint32_t zu_profile_now(){asm volatile("" ::: "memory"); uint32_t t=*(volatile uint32_t*)0xf8f00200u; asm volatile("" ::: "memory"); return t;}
extern unsigned long timeframes;
extern uint32_t gp_rng;
extern bool gp_active;
static bool gp_choose(){
 if(timeframes<3000)return false;
 gp_rng^=gp_rng<<13;gp_rng^=gp_rng>>17;gp_rng^=gp_rng<<5;return (gp_rng&63u)==0;
}
struct GpScope {
 unsigned stage; bool active; uint32_t start;
 GpScope(unsigned s,bool a):stage(s),active(a),start(a?zu_profile_now():0){}
 ~GpScope(){if(active){zu_profile_ticks[stage]+=(uint32_t)(zu_profile_now()-start);zu_profile_calls[stage]++;}}
};
struct GpFetch {
 bool saved;
 GpFetch(bool a):saved(gp_active){gp_active=a;}
 ~GpFetch(){gp_active=saved;}
};
#define ZU_PROFILE(stage) ((void)0)
void zu_profile_finish(void);
#else
#define ZU_PROFILE(stage) ((void)0)
static inline void zu_profile_finish(void){}
#endif

static_assert(ZU_PROFILE_BASE+16*ZU_PROFILE_STAGES<=0x482980u,"profile overlaps JIT report");
