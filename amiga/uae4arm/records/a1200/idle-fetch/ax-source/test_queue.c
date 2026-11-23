#include <assert.h>
#include <stdio.h>
#include "ax_queue.h"
int main(void){
 struct ax_queue q;unsigned i,n=0;ax_init(&q);
 assert(ax_free(&q)==0);ax_publish(&q,3);ax_publish(&q,4);ax_publish(&q,5);assert(ax_free(&q)<0);
 assert(ax_started(&q)==0);assert(q.completed==0);assert(ax_free(&q)<0);
 assert(ax_started(&q)==1);assert(q.completed==0);assert(ax_free(&q)<0);
 assert(ax_started(&q)==2);assert(q.completed==3);assert(ax_free(&q)==0);
 ax_publish(&q,6);assert(ax_started(&q)==0);assert(q.completed==7);
 assert(ax_started(&q)==3);assert(q.completed==12);assert(q.starvations==1);
 q.draining=1;
 assert(ax_started(&q)==3);assert(q.completed==18);assert(ax_idle(&q));assert(q.starvations==1);
 ax_init(&q);
 for(i=0;i<10000;i++){
  if(i%3 && ax_free(&q)>=0){ax_publish(&q,1+i%3072);n+=1+i%3072;}
  ax_started(&q);assert(q.completed<=n);assert(q.write<3 && q.read<3);
 }
 while(!ax_idle(&q))ax_started(&q);
 assert(q.completed==n);puts("PASS FIFO ownership, delayed retirement, silence underrun, exact counts, wrap/reuse");
}
