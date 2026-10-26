/* GPL-3.0-or-later. Adapted from ZZDosBox pc/scanline_plan.h.
 * Software brightness patterns only; no FPGA/firmware scanline control. */
#pragma once
#include <stdint.h>
/* Off, Soft, Smooth, Hard. Applied per output row. */
static inline unsigned ul_scan_level(unsigned mode,unsigned row){
    if(mode==1)return (row&1)?5:8;
    if(mode==2){const unsigned levels[4]={8,6,4,6};return levels[row&3];}
    if(mode==3)return (row&1)?0:8;
    return 8;
}
static inline uint32_t ul_scan_dim(uint32_t p,unsigned level){
    uint32_t lo=(((p&0x00ff00ffu)*level)>>3)&0x00ff00ffu;
    uint32_t hi=(((((p>>8)&0x00ff00ffu)*level)>>3)&0x00ff00ffu)<<8;
    return lo|hi;
}
static inline uint16_t ul_scan_565(uint16_t p,unsigned level){
    return ((((p>>11)*level)>>3)<<11)|
        (((((p>>5)&63)*level)>>3)<<5)|(((p&31)*level)>>3);
}
