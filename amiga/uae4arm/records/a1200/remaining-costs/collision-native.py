from pathlib import Path
import subprocess
p=Path('.context/amiga/uae4arm/a1200/remaining');source=Path('.context/amiga/uae4arm/a1200/gameplay/build-pixel4/src/custom.cpp').read_text()
a=source.index('static void do_sprite_collisions (void)\n{');z=source.index('\nstatic void record_sprite_1',a);old=source[a:z]
needle='''        for (l = k; match && l < planes; l += 2) {
          int t = 0;'''
assert old.count(needle)==1
new=old.replace(needle,'''        for (l = k; match && l < planes; l += 2) {
          if (!(clxcon_bpl_enable & (1 << l))) continue;
          int t = 0;''')
# Instrument only private line-data loads, not guest memory transactions.
old=old.replace('uae_u32 word = ldata[offs >> 5];','++reads; uae_u32 word = ldata[offs >> 5];').replace('do_sprite_collisions','reference')
new=new.replace('uae_u32 word = ldata[offs >> 5];','++reads; uae_u32 word = ldata[offs >> 5];').replace('do_sprite_collisions','candidate')
s='''#include <cstdint>
#include <cstdio>
#include <cstdlib>
using uae_u32=uint32_t; using hwres_t=int; using sprbuf_res_t=int;
const int MAX_WORDS_PER_LINE=128;
struct draw_info{int nr_sprites,first_sprite_entry;} curr_drawinfo[1];
struct decision{int plfleft,plfright,diwfirstword,diwlastword,nr_planes;} thisline_decision;
struct sprite_entry{int pos,max,first_pixel;} curr_sprite_entries[4];
int next_lineno,clxcon,bplcon0_res,sprite_buffer_res,aga_mode,bplcon0,clxcon_bpl_enable,clxcon_bpl_match,clxdat;
uint32_t clxmask[16],sprite_ab_merge[256];
uint16_t spixels[2048];
alignas(16) uint8_t line_data[1][8*2*MAX_WORDS_PER_LINE];
uint64_t reads;
static int coord_window_to_diw_x(int v){return v;}
static uint32_t rng=0x95a36718;
static uint32_t rnd(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
'''+old+'\n'+new+'''
int main(){
 for(int i=0;i<256;i++)sprite_ab_merge[i]=((i&15)?1:0)|((i&240)?2:0);
 uint64_t before=0,after=0;
 for(int test=0;test<200000;test++){
  for(auto &x:clxmask)x=rnd()&65535;
  for(auto &x:spixels)x=rnd();
  for(auto &x:line_data[0])x=rnd();
  clxcon=(rnd()&15)<<12; bplcon0_res=rnd()%3; sprite_buffer_res=rnd()%3;
  aga_mode=rnd()&1;bplcon0=(rnd()&1)*0x400;
  clxcon_bpl_enable=test%256;clxcon_bpl_match=rnd()&255;
  thisline_decision={0,64,0,128,int(rnd()%9)};
  curr_drawinfo[0]={int(rnd()%5),0};
  for(int i=0;i<4;i++){
   int pos=rnd()%48,max=pos+1+rnd()%64;
   curr_sprite_entries[i]={pos<<sprite_buffer_res,max<<sprite_buffer_res,i*512};
  }
  int initial=rnd()&0x1ff;clxdat=initial;reads=0;reference();int expected=clxdat;before+=reads;
  clxdat=initial;reads=0;candidate();after+=reads;
  if(clxdat!=expected){printf("FAIL case=%d expected=%x actual=%x\\n",test,expected,clxdat);return 1;}
  if(!clxcon_bpl_enable&&reads){puts("FAIL disabled planes read");return 1;}
 }
 printf("PASS 200000 collision comparisons; private buffer reads reference=%llu candidate=%llu\\n",(unsigned long long)before,(unsigned long long)after);
}
'''
(p/'collision-native.cpp').write_text(s)
subprocess.run(['clang++','-std=c++11','-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'collision-native.cpp'),'-o',str(p/'collision-native')],check=True)
subprocess.run([str(p/'collision-native')],check=True)
