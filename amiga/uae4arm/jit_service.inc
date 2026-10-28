/* Included before do_specialties only in a sampled diagnostic build. */
#include "jit_profile.h"
static inline uint32_t zzuae_jit_profile_clock(){return *(volatile uint32_t*)0xf8f00200u;}
static ZuJitProfile zz_jit_profile={0x73c4a921u};
static bool zz_jit_service_active;
