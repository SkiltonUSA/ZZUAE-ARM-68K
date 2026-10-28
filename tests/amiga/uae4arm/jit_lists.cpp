#include <cassert>
#include <cstdint>
#include <vector>
#include <algorithm>
#define STATIC_INLINE static inline
using uae_u32=unsigned;
using cpuop_func=void();
struct blockinfo {
 void *pc_p;cpuop_func *handler_to_use;
 blockinfo *next_same_cl,**prev_same_cl_p,*next,**prev_p;
};
struct Tag {blockinfo *bi;cpuop_func *handler;};
static Tag cache_tags[16];
static blockinfo *active,*dormant;
static unsigned cacheline(void *p){return (uintptr_t)p&14;}
static void popall_execute_normal(){}
static void first(){}static void second(){}
#include "jit_lists_generated.inc"
int main(){
 blockinfo blocks[12]={};std::vector<blockinfo*> expected[8];
 for(unsigned i=0;i<12;i++){
  blockinfo *b=&blocks[i];b->pc_p=(void*)(uintptr_t)((i%8)*2);b->handler_to_use=first;
  add_to_cl_list(b);expected[i%8].insert(expected[i%8].begin(),b);
 }
 unsigned random=1;
 for(unsigned n=0;n<10000;n++){
  random=random*1664525+1013904223;blockinfo *b=&blocks[random%12];
  // Includes a changed handler on an entry already at the bucket head.
  b->handler_to_use=(n&1)?first:second;
  auto &list=expected[cacheline(b->pc_p)/2];
  list.erase(std::find(list.begin(),list.end(),b));list.insert(list.begin(),b);
  raise_in_cl_list(b);
  for(unsigned cl=0;cl<16;cl+=2){
   blockinfo **prev=&cache_tags[cl+1].bi;auto &want=expected[cl/2];
   for(auto *item:want){assert(*prev==item);assert(item->prev_same_cl_p==prev);prev=&item->next_same_cl;}
   assert(*prev==nullptr);assert(cache_tags[cl].handler==want.front()->handler_to_use);
  }
 }
}
