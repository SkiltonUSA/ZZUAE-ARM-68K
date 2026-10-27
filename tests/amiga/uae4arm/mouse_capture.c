#include "mouse_capture_plan.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 struct um_queue q={0};struct um_event e;int dx=0,dy=0;
 q.head=q.tail=UINT32_MAX-4;q.active=1;
 /* Motion and transitions keep their order, including sequence wrap. */
 for(unsigned i=0;i<12;i++)assert(um_push(&q,20,-15,i==0?0x68:i==11?0xe8:0xff));
 for(unsigned i=0;i<12;i++){
  assert(um_pop(&q,&e));dx+=e.x;dy+=e.y;
  assert(e.code==(i==0?0x68:i==11?0xe8:0xff));
 }
 assert(dx==240&&dy==-180&&!um_pop(&q,&e));
 /* Saturation releases capture instead of leaving a swallowed button held. */
 for(unsigned i=0;i<UM_CAPACITY;i++)assert(um_push(&q,1,0,0xff));
 assert(!um_push(&q,0,0,0xe8)&&!q.active&&q.overflow==1);
 um_reset(&q);assert(!um_pop(&q,&e));
 q.active=1;assert(um_push(&q,-1,2,0x69));um_reset(&q);
 assert(!q.active&&!um_pop(&q,&e));
 puts("PASS: captured mouse motion/button order, counter wrap, overflow release and reset");
}
