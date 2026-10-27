/* Integer-only RGB565 presentation. Keep FP/NEON out of this worker until its
 * context contract supports them. Scalar reference lives in live_pixels.h. */
#pragma once
#include "live_pixels.h"
#include "scanlines.h"
template<unsigned Format,bool Dim,bool Mapped>
static void ul_convert_row(uint32_t *out,const uint16_t *src,
                           const unsigned short *map,unsigned width,unsigned level){
    for(unsigned x=0;x<width;x++){
        uint32_t p=ul_pixel(src[Mapped?map[x]:x],Format);
        out[x]=Dim?ul_scan_dim(p,level):p;
    }
}
template<unsigned Format,bool Mapped>
static void ul_convert_row_level(uint32_t *out,const uint16_t *src,
                                 const unsigned short *map,unsigned width,unsigned level){
    if(level==8)ul_convert_row<Format,false,Mapped>(out,src,map,width,level);
    else ul_convert_row<Format,true,Mapped>(out,src,map,width,level);
}
static void ul_prepare_row(uint32_t *out,const uint16_t *src,
                           const unsigned short *map,unsigned width,unsigned format,unsigned level){
    if(!level){for(unsigned x=0;x<width;x++)out[x]=0;return;}
    if(width==640){
        if(format==3)ul_convert_row_level<3,false>(out,src,map,width,level);
        else ul_convert_row_level<4,false>(out,src,map,width,level);
    }else{
        if(format==3)ul_convert_row_level<3,true>(out,src,map,width,level);
        else ul_convert_row_level<4,true>(out,src,map,width,level);
    }
}
