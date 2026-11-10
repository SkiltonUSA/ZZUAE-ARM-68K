#include <cassert>
#include <initializer_list>
#include "../../../amiga/uae4arm/render_cadence.inc"
int main(){
 for(unsigned hz: {50u,60u})for(unsigned rate: {25u,30u,50u,60u,0u}){
  unsigned phase=0,count=0;
  for(unsigned frame=0;frame<3000;frame++){
   bool draw=zu_render_due(rate,phase,hz);
   count+=draw;
   assert(phase<hz);
   assert(count==((rate && rate<hz)?((frame+1)*rate/hz):(frame+1)));
  }
 }
}
