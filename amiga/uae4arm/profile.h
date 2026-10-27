/* Optional diagnostic timers; never enabled in normal/release builds.
 * Inclusive stages overlap (drawing includes bitplanes AND presentation;
 * audio includes PCM publication; presentation includes conversion).
 * Do not sum their shares. Timers include waiting, not just busy CPU work. */
#pragma once
#include <stdint.h>
#define ZU_PROFILE_BASE 0x482900u
#define ZU_PROFILE_STAGES 6u
#ifdef ZZUAE_PROFILE
extern uint64_t zu_profile_ticks[ZU_PROFILE_STAGES];
extern uint32_t zu_profile_calls[ZU_PROFILE_STAGES];
static inline uint32_t zu_profile_now(){return *(volatile uint32_t*)0xf8f00200u;}
struct ZuProfileScope {
    unsigned stage; uint32_t start;
    explicit ZuProfileScope(unsigned s):stage(s),start(zu_profile_now()){}
    ~ZuProfileScope(){zu_profile_ticks[stage]+=(uint32_t)(zu_profile_now()-start);zu_profile_calls[stage]++;}
};
#define ZU_PROFILE(stage) ZuProfileScope zu_profile_scope(stage)
void zu_profile_finish(void);
#else
#define ZU_PROFILE(stage) ((void)0)
static inline void zu_profile_finish(void){}
#endif
