#pragma once
#include <stdint.h>
/* One Zorro-II RAM board, advertised using UAE's established autoconfig layout. */
static inline uint32_t zu_fast_size(unsigned selection) {
 return selection && selection<=3 ? (0x100000u<<selection) : 0;
}
static inline unsigned zu_fast_type(uint32_t size) {
 return 0xe0u | (size==0x200000u?6u:size==0x400000u?7u:0u);
}
static inline uint8_t zu_fast_config_byte(uint32_t size,unsigned offset) {
 unsigned reg=offset&~3u, value=0;
 if(reg>0x40 || (offset&1))return 0xff;
 if(reg==0)value=zu_fast_type(size);
 else if(reg==4)value=81; /* UAE RAM board product */
 else if(reg==0x10)value=0x07;
 else if(reg==0x14)value=0xdb; /* UAE manufacturer 2011 */
 else if(reg==0x24)value=1;
 unsigned nibble=(offset&2)?(value&15)<<4:value&0xf0;
 return reg==0 || reg==0x40?nibble:(uint8_t)~nibble;
}
