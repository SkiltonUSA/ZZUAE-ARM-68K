#include "profile.h"
#ifdef ZZUAE_PROFILE
#include "machine.h"
#include "protocol.h"
uint64_t zu_profile_ticks[ZU_PROFILE_STAGES];
uint32_t zu_profile_calls[ZU_PROFILE_STAGES];
void zu_profile_finish(void){
    for(unsigned i=0;i<ZU_PROFILE_STAGES;i++){
        ad_put(uae_shared,ZU_PROFILE_BASE+16*i,(uint32_t)(zu_profile_ticks[i]>>32));
        ad_put(uae_shared,ZU_PROFILE_BASE+16*i+4,(uint32_t)zu_profile_ticks[i]);
        ad_put(uae_shared,ZU_PROFILE_BASE+16*i+8,zu_profile_calls[i]);
    }
}
#endif

uint32_t gp_rng[6]={0x73c4a921,0x87654321,0x2917bb13,0x81517a31,0x12345678,0x78de2191};
bool gp_sprite_record;
