#include "convert_row.h"
#include "aspect.h"
#include <cassert>
#include <cstdio>
#include <vector>
int main(){
 for(unsigned width=320;width<=640;width+=4){
  unsigned short map[640];ul_scale_map(map,width,640);
  std::vector<uint16_t> src(640);
  std::vector<uint32_t> dst(width+2);
  for(unsigned start=0;start<65536;start+=640){
   for(unsigned x=0;x<640;x++)src[x]=(uint16_t)(start+x);
   for(unsigned format: {3u,4u})for(unsigned level: {0u,4u,5u,6u,8u}){
    dst.front()=0x12345678;dst.back()=0xabcdef01;
    ul_prepare_row(dst.data()+1,src.data(),map,width,format,level);
    for(unsigned x=0;x<width;x++)assert(dst[x+1]==ul_scan_dim(ul_pixel(src[map[x]],format),level));
    assert(dst.front()==0x12345678 && dst.back()==0xabcdef01);
   }
  }
 }
 puts("PASS: row conversion matches scalar reference: RGB565 space, both byte orders, all supported widths and brightness levels");
}
