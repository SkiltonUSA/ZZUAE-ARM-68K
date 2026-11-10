#include <cstdint>
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
static void reference (int sprxp, uae_u16 *buf, uae_u32 datab, int num, int dbl,
  unsigned int mask, int do_collisions, uae_u32 collision_mask)
{
  int j = 0;
  while (datab) {
    unsigned int col = 0;
    unsigned int coltmp = 0;

    if ((sprxp >= sprite_minx && sprxp < sprite_maxx) || (bplcon3 & 2))
      col = (datab & 3) << (2 * num);
    if ((j & mask) == 0) {
      unsigned int tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      sprxp++;
    }
    if (dbl > 0) {
      unsigned int tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      sprxp++;
    }
    if (dbl > 1) {
      unsigned int tmp;
      tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      sprxp++;
      sprxp++;
    }
    j++;
    datab >>= 2;
    if (do_collisions) {
      coltmp &= collision_mask;
      if (coltmp) {
        unsigned int shrunk_tmp = sprite_ab_merge[coltmp & 255] | (sprite_ab_merge[coltmp >> 8] << 2);
        clxdat |= sprclx[shrunk_tmp];
      }
    }
  }
}

static void candidate (int sprxp, uae_u16 *buf, uae_u32 datab, int num, int dbl,
  unsigned int mask, int do_collisions, uae_u32 collision_mask)
{
    if (zu_sprite_neon_ready && datab && !do_collisions && mask == 0
        && dbl >= 0 && dbl <= 2
        && ((bplcon3 & 2) || (sprxp >= sprite_minx && sprxp + (16 << dbl) <= sprite_maxx))) {
        zu_sprite_or16(buf, datab, 2 * num, dbl);
        ++zu_sprite_neon_spans;
        return;
    }

  int j = 0;
  while (datab) {
    unsigned int col = 0;
    unsigned int coltmp = 0;

    if ((sprxp >= sprite_minx && sprxp < sprite_maxx) || (bplcon3 & 2))
      col = (datab & 3) << (2 * num);
    if ((j & mask) == 0) {
      unsigned int tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      sprxp++;
    }
    if (dbl > 0) {
      unsigned int tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      sprxp++;
    }
    if (dbl > 1) {
      unsigned int tmp;
      tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      tmp = (*buf) | col;
      *buf++ = tmp;
      if (do_collisions)
        coltmp |= tmp;
      sprxp++;
      sprxp++;
    }
    j++;
    datab >>= 2;
    if (do_collisions) {
      coltmp &= collision_mask;
      if (coltmp) {
        unsigned int shrunk_tmp = sprite_ab_merge[coltmp & 255] | (sprite_ab_merge[coltmp >> 8] << 2);
        clxdat |= sprclx[shrunk_tmp];
      }
    }
  }
}

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
  if(expected!=clxdat||memcmp(a,b,sizeof(a))){printf("FAIL %d\n",trial);return 1;}
 }
 if(!zu_sprite_neon_spans)return 2;
 printf("PASS 500000 sprite buffer/clipping/collision/availability comparisons; fast spans=%u\n",zu_sprite_neon_spans);
}
