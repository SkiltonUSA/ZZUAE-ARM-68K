#pragma once
#include <stdint.h>
/* Uncached transport, distinct producer/consumer lines; one outstanding IO.
 * Up to 32 sectors per request. Host never touches guest RAM directly. */
#define US_CONTROL 0x483100u
#define US_REQUEST (US_CONTROL+0u)
#define US_OPERATION (US_CONTROL+4u)
#define US_UNIT (US_CONTROL+8u)
#define US_OFFSET (US_CONTROL+12u)
#define US_LENGTH (US_CONTROL+16u)
#define US_REPLY (US_CONTROL+64u)
#define US_RESULT (US_CONTROL+68u)
#define US_HDF_SIZE (US_CONTROL+72u)
#define US_WRITABLE (US_CONTROL+76u)
#define US_OFFSET_HIGH (US_CONTROL+20u)
#define US_USB_DISK (US_CONTROL+80u)
#define US_HDF_HIGH (US_CONTROL+84u)
#define US_DATA 0x488000u
#define US_CAPACITY 16384u
#define US_READ 1u
#define US_WRITE 2u
static inline int us_bounds(uint32_t total,uint32_t offset,uint32_t size){
 return size && size<=US_CAPACITY && !(size&511u) && !(offset&511u) && offset<=total && size<=total-offset;
}
static inline int us_bounds64(uint64_t total,uint64_t offset,uint32_t size){
 return size && size<=US_CAPACITY && !(size&511u) && !(offset&511u) && offset<=total && size<=total-offset;
}
