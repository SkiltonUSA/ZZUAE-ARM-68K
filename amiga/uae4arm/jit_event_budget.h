#pragma once
#include <stdint.h>
/* Zero means no grouped block. Unsigned distance handles cycle-counter wrap. */
static inline bool zzuae_group_fits(uint32_t cycles,uint32_t now,uint32_t next,bool pending=false) {
 return !cycles || (!pending && cycles<=next-now);
}
