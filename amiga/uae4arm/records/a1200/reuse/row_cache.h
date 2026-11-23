#pragma once
#include <stdint.h>
#include <string.h>
/* Private conversion cache. Never records a display bitmap pointer or skips
 * delivery. Source comparison happens after all guest rendering is complete. */
struct RowCache {
 uint16_t source[256][640] __attribute__((aligned(4)));
 uint32_t pixels[256][640];
 unsigned width,format,height;
 bool valid[256];
 void configure(unsigned w,unsigned f,unsigned h){
  if(w==width&&f==format&&h==height)return;
  width=w;format=f;height=h;memset(valid,0,sizeof valid);
 }
 bool hit(unsigned row,const uint16_t *current){
  if(!valid[row])return false;
  // Cache and renderer rows are word-aligned private memory.
  typedef uint32_t word __attribute__((__may_alias__));
  const word *a=(const word*)source[row],*b=(const word*)current;
  const uint32_t mask=width==320?0xffffu:0xffffffffu;
  for(unsigned x=0;x<320;x+=4)
   if(((a[x]^b[x])|(a[x+1]^b[x+1])|(a[x+2]^b[x+2])|(a[x+3]^b[x+3]))&mask)return false;
  return true;
 }
 void remember(unsigned row,const uint16_t *current){
  memcpy(source[row],current,640*2);valid[row]=true;
 }
};
