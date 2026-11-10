#include "storage_wire.h"
#include <assert.h>
#include <stdio.h>
int main(void){uint64_t size=31914983424ULL;
 assert(us_bounds64(size,0,512));assert(us_bounds64(size,0x80000000ULL,512));assert(us_bounds64(size,0x100000000ULL,16384));
 assert(us_bounds64(size,size-512,512));assert(!us_bounds64(size,size,512));assert(!us_bounds64(size,UINT64_MAX-511,512));
 assert(!us_bounds64(size,1,512));assert(!us_bounds64(size,512,513));assert(!us_bounds64(size,0,32768));
 puts("PASS physical storage bounds above 2/4 GiB, final sector, overflow and alignment");return 0;}
