/* PCM queue in application-owned, noncacheable DDR. Counters and PCM are BE.
 * Producer publishes complete 1024-frame blocks; consumer releases after copy. */
#pragma once
#include <stdint.h>
#define UA_CONTROL 0x483000u
#define UA_WRITE (UA_CONTROL+0u)
#define UA_READ (UA_CONTROL+64u)
#define UA_RATE (UA_CONTROL+68u)
#define UA_NONZERO (UA_CONTROL+4u)
#define UA_DEFERRED (UA_CONTROL+8u)
#define UA_RESERVE (UA_CONTROL+72u)
#define UA_PACING (UA_CONTROL+76u)
#define UA_FRAMES 1024u
#define UA_SLOTS 4u
#define UA_STRIDE (UA_FRAMES*4u)
#define UA_DATA 0x484000u
#define UAE_OPT_AUDIO 64u
#if UA_DATA+UA_SLOTS*UA_STRIDE > 0x490000u
#error PCM overlaps video staging
#endif
static inline int ua_room(uint32_t write,uint32_t read){return (uint32_t)(write-read)<UA_SLOTS;}
static inline void ua_pcm(uint8_t *p,uint16_t left,uint16_t right){
 p[0]=left>>8;p[1]=left;p[2]=right>>8;p[3]=right;
}

/* Reserve is an estimate in complete PCM blocks, not a playback timestamp.
 * Limit consecutive skips so the UI still refreshes under sustained overload. */
static inline int ua_defer_display(unsigned published,unsigned reserve,unsigned streak){
 return published && reserve<3u*UA_FRAMES && streak<3u;
}
