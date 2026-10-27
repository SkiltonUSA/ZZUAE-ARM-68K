/* GPL-3.0-or-later. Experimental Core1-local executable cache.
 * Not a guest JIT implementation. The normal player does not link this file. */
#pragma once
#include <stdint.h>
#include "jit_config.h"
/* Include the translator's entry/exit stubs and page-alignment headroom. */
#define ZJ_CAPACITY (ZU_JIT_CACHE_KIB == 512 ? 0x100000u : 0x2010000u)
#define ZJ_REPORT 0x482a00u
static inline int zj_span(uint32_t base,uint32_t size,uint32_t at,uint32_t count){
 return count && at>=base && at-base<size && count<=size-(at-base);
}
#ifdef __cplusplus
extern "C" {
#endif
void *zzuae_jit_alloc_executable(unsigned);
void zzuae_jit_free_executable(void*,unsigned);
void zzuae_jit_publish_code(void*,void*);
unsigned zzuae_jit_cache_selftest(void);
#ifdef __cplusplus
}
#endif
