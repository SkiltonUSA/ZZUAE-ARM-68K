#include <cassert>
#include <initializer_list>
#include "../../../amiga/uae4arm/render_cadence.inc"
int main(){
 for(unsigned rate: {25u,30u,50u,0u}){
  unsigned phase=0,count=0;
  for(unsigned frame=0;frame<3000;frame++){
   bool draw=zu_render_due(rate,phase);
   count+=draw;
   assert(phase<50);
   assert(count==((rate && rate<50)?((frame+1)*rate/50):(frame+1)));
  }
 }
}
