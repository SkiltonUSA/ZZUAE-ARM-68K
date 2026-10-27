/* GPL-3.0-or-later. Experimental Core1-local executable cache.
 * Not a guest JIT implementation. The normal player does not link this file. */
#pragma once
#include <stdint.h>
#define ZJ_CAPACITY 0x100000u
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
