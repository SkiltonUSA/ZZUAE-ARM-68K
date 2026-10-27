#include "presentation.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 struct ul_fps f={0};ul_fps_start(&f,0xfffffff0u);
 for(unsigned i=1;i<=30;i++)ul_fps_frame(&f,0xfffffff0u+i*33334u);
 assert(f.tenths==300);
 ul_fps_frame(&f,0xfffffff0u+3000000u);assert(f.tenths==5);
 puts("PASS: measured FPS across timer wrap/stalls");
}
