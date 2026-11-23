#pragma once
#include <stdint.h>
struct RepeatStats { uint32_t rows,full_rows,visible_rows,spans,full_spans,visible_spans; };
/* Compare final RGB565 pixels, not guest memory hashes. Every previous pixel
 * is updated even on a miss. A 320-wide output uses the even source pixels. */
static inline void repeat_row(RepeatStats &s,uint16_t *previous,const uint16_t *current,unsigned stride,bool valid){
 bool full=true,visible=true;
 for(unsigned x=0;x<640;x+=32){
  bool a=valid,b=valid;
  for(unsigned i=0;i<32;i++){
   bool equal=previous[x+i]==current[x+i];
   a=a&&equal;if(i%stride==0)b=b&&equal;
   previous[x+i]=current[x+i];
  }
  ++s.spans;s.full_spans+=a;s.visible_spans+=b;
  full=full&&a;visible=visible&&b;
 }
 ++s.rows;s.full_rows+=full;s.visible_rows+=visible;
}
