/* A32 B/BL uses a signed 24-bit word displacement from PC+8. */
#include <stdint.h>
static inline int zj_branch(uint32_t instruction,uint32_t from,uint32_t to,uint32_t *out){
 int64_t delta=(int64_t)to-from-8;
 if((delta&3) || delta < -0x2000000 || delta > 0x1fffffc)return 0;
 *out=(instruction&0xff000000u)|((uint32_t)(delta/4)&0xffffffu);
 return 1;
}
