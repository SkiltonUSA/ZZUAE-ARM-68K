from pathlib import Path
import subprocess
p=Path(__file__).resolve().parent
s=(p.parent/'gameplay/build-pixel4/src/custom.cpp').read_text()
a=s.index('static void record_sprite_1 (');z=s.index('\n/* DATAB contains',a);old=s[a:z]
new=old.replace('record_sprite_1','candidate');i=new.index('{')+1
new=new[:i]+'\n'+(p/'entry.inc').read_text()+new[i:]
source='''#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
using uae_u32=uint32_t;using uae_u16=uint16_t;
int sprite_minx,sprite_maxx,bplcon3;unsigned clxdat;unsigned sprite_ab_merge[256],sprclx[16];
bool zu_sprite_neon_ready;unsigned zu_sprite_neon_spans;
static uint32_t rng=0xac96325f;
static uint32_t rnd(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
// Scalar specification of the separately instruction-tested assembly leaf.
void zu_sprite_or16(uae_u16 *buf,uae_u32 data,unsigned shift,unsigned scale){
 for(unsigned i=0;i<16;++i)for(unsigned n=0;n<(1u<<scale);++n)
  buf[(i<<scale)+n]|=((data>>(2*i))&3)<<shift;
}
'''+old.replace('record_sprite_1','reference')+'\n'+new+'''
int main(){
 for(int i=0;i<256;i++)sprite_ab_merge[i]=((i&15)?1:0)|((i&240)?2:0);
 for(auto &v:sprclx)v=rnd()&65535;
 for(int trial=0;trial<500000;trial++){
  uae_u16 a[96],b[96];for(auto &v:a)v=rnd();memcpy(b,a,sizeof(a));
  int x=int(rnd()%300)-30; sprite_minx=rnd()%100;sprite_maxx=sprite_minx+rnd()%400;
  bplcon3=(rnd()&1)*2;unsigned data=rnd(); if(trial%17==0)data=0;if(trial%19==0)data&=255;
  int num=rnd()%8,dbl=rnd()%3,collision=rnd()&1;unsigned mask=(rnd()%3)?0:(2u<<(rnd()&1));
  unsigned cm=rnd()&65535,initial=rnd()&65535;zu_sprite_neon_ready=(trial%5)!=0;
  clxdat=initial;reference(x,a+16,data,num,dbl,mask,collision,cm);unsigned expected=clxdat;
  clxdat=initial;candidate(x,b+16,data,num,dbl,mask,collision,cm);
  if(expected!=clxdat||memcmp(a,b,sizeof(a))){printf("FAIL %d\\n",trial);return 1;}
 }
 if(!zu_sprite_neon_spans)return 2;
 printf("PASS 500000 sprite buffer/clipping/collision/availability comparisons; fast spans=%u\\n",zu_sprite_neon_spans);
}
'''
source='\n'.join(line.expandtabs(2).rstrip() for line in source.splitlines())+'\n'
(p/'native.cpp').write_text(source)
subprocess.run(['clang++','-std=c++11','-O2','-fsanitize=address,undefined','-fno-sanitize-recover=all',str(p/'native.cpp'),'-o',str(p/'native')],check=True)
subprocess.run([str(p/'native')],check=True)
