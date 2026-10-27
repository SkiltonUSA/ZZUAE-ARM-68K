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
