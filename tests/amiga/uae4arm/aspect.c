#include "aspect.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 assert(ul_view_valid(320,256));
 assert(ul_view_valid(640,512));
 assert(!ul_view_valid(640,513));
 unsigned w=0,h=0;unsigned short map[640];
 ul_scale_map(map,640,640);for(unsigned x=0;x<640;x++)assert(map[x]==x);
 ul_scale_map(map,512,256);for(unsigned y=0;y<512;y++)assert(map[y]==y/2);
 assert(ul_view_size(1888,725,&w,&h)&&w==640&&h==480);
 assert(ul_view_size(608,416,&w,&h)&&w==552&&h==414);
 assert(ul_view_size(320,240,&w,&h)&&w==320&&h==240);
 assert(!ul_view_size(319,240,&w,&h));
 assert(!ul_view_valid(320,255)&&!ul_view_valid(644,483));
 for(unsigned n=80;n<=160;n++){
  w=n*4;h=n*3;assert(ul_view_valid(w,h));
  ul_scale_map(map,w,640);for(unsigned x=0;x<w;x++)assert(map[x]==x*640/w);
  ul_scale_map(map,h,256);for(unsigned y=0;y<h;y++)assert(map[y]==y*256/h);
  int rx=0,ry=0,sx=0,sy=0;
  for(unsigned i=0;i<w;i++)sx+=ul_mouse_scale(1,320,w,&rx);
  for(unsigned i=0;i<h;i++)sy+=ul_mouse_scale(1,256,h,&ry);
  assert(sx==320&&sy==256&&!rx&&!ry);
  for(unsigned i=0;i<w;i++)sx+=ul_mouse_scale(-1,320,w,&rx);
  for(unsigned i=0;i<h;i++)sy+=ul_mouse_scale(-1,256,h,&ry);
  assert(!sx&&!sy&&!rx&&!ry);
 }
 puts("PASS: 4:3 screen fit, exact scaling maps and reversible fractional mouse movement");
}
