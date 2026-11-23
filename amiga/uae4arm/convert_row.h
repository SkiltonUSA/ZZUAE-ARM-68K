/* Full-brightness RGB565 presentation. Scanlines belong to the FPGA. */
#pragma once
#include "live_pixels.h"
/* Two RGB565 pixels per ARM word, in P96's big-endian byte order. Source
 * samples and scaling stay identical to the 32-bit path. Width is even. */
static inline void ul_prepare_row565(uint32_t *out,const uint16_t *src,
                              const unsigned short *map,unsigned width){
    for(unsigned x=0;x<width;x+=2){
        uint32_t a=src[map[x]],b=src[map[x+1]];
        out[x/2]=((a>>8)&255)|((a&255)<<8)|((b>>8)<<16)|((b&255)<<24);
    }
}
template<unsigned Format,bool Mapped>
static void ul_convert_row(uint32_t *out,const uint16_t *src,
                           const unsigned short *map,unsigned width){
    for(unsigned x=0;x<width;x++)out[x]=ul_pixel(src[Mapped?map[x]:x],Format);
}
static void ul_prepare_row(uint32_t *out,const uint16_t *src,
                           const unsigned short *map,unsigned width,unsigned format){
    if(width==640){
        if(format==3)ul_convert_row<3,false>(out,src,map,width);
        else ul_convert_row<4,false>(out,src,map,width);
    }else{
        if(format==3)ul_convert_row<3,true>(out,src,map,width);
        else ul_convert_row<4,true>(out,src,map,width);
    }
}
