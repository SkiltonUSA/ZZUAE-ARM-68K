#include "repeat_probe.h"
#include <cassert>
#include <cstring>
#include <cstdio>
int main(){
 uint16_t old[640]={},current[640]={};RepeatStats s={};
 repeat_row(s,old,current,2,false);assert(s.rows==1&&s.full_rows==0&&s.visible_spans==0);
 repeat_row(s,old,current,2,true);assert(s.full_rows==1&&s.visible_rows==1&&s.full_spans==20);
 current[3]=123;repeat_row(s,old,current,2,true);assert(s.full_rows==1&&s.visible_rows==2&&s.full_spans==39&&s.visible_spans==40);
 current[638]=456;repeat_row(s,old,current,2,true);assert(s.full_rows==1&&s.visible_rows==2&&s.full_spans==58&&s.visible_spans==59);
 repeat_row(s,old,current,1,true);assert(s.full_rows==2&&s.visible_rows==3);
 uint32_t r=1;
 for(unsigned n=0;n<10000;n++){
  unsigned stride=1+n%2;bool valid=n%37!=0;
  if(n%3){r=r*1664525u+1013904223u;current[r%640]^=r>>16;}
  RepeatStats expected=s;bool full=valid,visible=valid;
  for(unsigned x=0;x<640;x+=32){
   bool a=valid&&!memcmp(old+x,current+x,64),b=valid;
   for(unsigned i=0;i<32;i+=stride)if(old[x+i]!=current[x+i])b=false;
   ++expected.spans;expected.full_spans+=a;expected.visible_spans+=b;full&=a;visible&=b;
  }
  ++expected.rows;expected.full_rows+=full;expected.visible_rows+=visible;
  repeat_row(s,old,current,stride,valid);
  assert(!memcmp(&s,&expected,sizeof s));assert(!memcmp(old,current,sizeof old));
 }
 puts("PASS cold cache, unchanged rows, odd/even pixels, last pixel, 10000 history comparisons");
}
