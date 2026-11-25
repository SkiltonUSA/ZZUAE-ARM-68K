#include <assert.h>
#include <stdio.h>
#include "../../../amiga/common/rtg_mapping.h"
static uint32_t l1[4096],l2[RTG_TABLE_COUNT*256];
int main(void){
 const uint32_t address=0x002fff00,table=0x600000;
 assert(rtg_bpp(RTG_RGB565_BE)==2);
 assert(rtg_span_size(address,640,RTG_RGB565_BE,320,240)==153600);
 assert(!rtg_span_size(address,636,RTG_RGB565_BE,320,240));
 assert(!rtg_span_size(RTG_APERTURE_END-153596,640,RTG_RGB565_BE,320,240));
 assert(rtg_map_size(l1,l2,table,address,640,RTG_RGB565_BE,320,240));
 assert(l1[2]==(table|1)&&l1[3]==((table+1024)|1));
 assert(l2[255]==((address&~4095u)|RTG_PAGE));
 assert(l2[256]==(0x00300000u|RTG_PAGE));
 assert(!rtg_map_size(l1,l2,table,address,640,RTG_RGB565_BE,320,240));
 rtg_unmap(l1,address,153600);assert(!l1[2]&&!l1[3]);
 assert(rtg_bpp(RTG_ARGB32)==4&&rtg_bpp(RTG_BGRA32)==4&&rtg_bpp(RTG_RGB24)==3&&!rtg_bpp(6));
 puts("PASS RGB565 mapping: pitch/span/aperture, cross-section page map, occupied mapping refusal and unmap");
}
