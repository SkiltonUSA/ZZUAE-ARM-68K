#pragma once
#include <stdint.h>
/* Return the little-endian ARM word for the selected P96 byte order. */
static inline uint32_t ul_pixel(uint16_t c,unsigned format) {
    uint32_t r=c>>11,g=(c>>5)&63,b=c&31;
    r=(r<<3)|(r>>2);g=(g<<2)|(g>>4);b=(b<<3)|(b>>2);
    return format==3 ? 0xff000000u|(r<<16)|(g<<8)|b : (b<<24)|(g<<16)|(r<<8)|255;
}
