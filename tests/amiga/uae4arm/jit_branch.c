#include <assert.h>
#include <stdint.h>
#include "jit_branch.inc"
int main(void){
 uint32_t out=0,at=0x14000000;
 assert(zj_branch(0xea000000,at,at+8,&out) && out==0xea000000);
 assert(zj_branch(0x1a000000,at,at+8+0x1fffffc,&out) && out==0x1a7fffff);
 assert(zj_branch(0x0a000000,at,at+8-0x2000000,&out) && out==0x0a800000);
 assert(!zj_branch(0xea000000,at,at+8+0x2000000,&out));
 assert(!zj_branch(0xea000000,at,at+8-0x2000004,&out));
 assert(!zj_branch(0xea000000,at,at+9,&out));
 return 0;
}
