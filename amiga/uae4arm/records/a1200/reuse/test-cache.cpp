#include "row_cache.h"
#include "convert_row.h"
#include <cassert>
#include <cstdio>
static RowCache cache;
int main(){
 alignas(4) uint16_t src[640]={};uint32_t expected[640];unsigned short map[640];
 uint32_t r=27;unsigned hits=0,misses=0;
 for(unsigned n=0;n<10000;n++){
  unsigned w=(n/37)%2?640:320,f=(n/41)%2?3:4,h=(n/43)%2?240:256,y=(n/5)%h;
  cache.configure(w,f,h);
  for(unsigned x=0;x<w;x++)map[x]=x*(640/w);
  if(n%3){r=r*1664525+1013904223;src[r%640]^=r>>16;}
  if(cache.hit(y,src))++hits;
  else {++misses;ul_prepare_row(cache.pixels[y],src,map,w,f);cache.remember(y,src);}
  ul_prepare_row(expected,src,map,w,f);
  assert(!memcmp(expected,cache.pixels[y],w*4));
 }
 assert(hits>100 && misses>100);
 cache.configure(320,3,256);assert(!cache.hit(0,src));cache.remember(0,src);assert(cache.hit(0,src));
 src[1]^=1;assert(cache.hit(0,src));src[638]^=1;assert(!cache.hit(0,src));
 cache.configure(640,3,256);assert(!cache.hit(0,src));cache.remember(0,src);assert(cache.hit(0,src));src[639]^=1;assert(!cache.hit(0,src));
 cache.configure(640,4,256);assert(!cache.hit(0,src));cache.remember(0,src);
 cache.configure(640,4,240);assert(!cache.hit(0,src));
 puts("PASS conversion equivalence, format/size/height invalidation, visible pixel boundaries");
}
