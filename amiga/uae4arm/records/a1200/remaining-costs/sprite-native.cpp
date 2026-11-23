#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cstdlib>
using uae_u32=uint32_t;using uae_u16=uint16_t;
int sprite_minx,sprite_maxx,bplcon3;unsigned clxdat;unsigned sprite_ab_merge[256],sprclx[16];
unsigned fast;
static uint32_t rng=0xac96325f;
static uint32_t rnd(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
/* Private experiment: only unclipped, unmasked, non-collision spans. */
template<int Dup> static inline void zz_sprite_plain(uae_u16 *buf, uae_u32 datab, int num)
{
    while (datab) {
        unsigned col = (datab & 3) << (2 * num);
        for (int i = 0; i < (1 << Dup); ++i) buf[i] |= col;
        buf += 1 << Dup;
        datab >>= 2;
    }
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
    if (!do_collisions && !mask && dbl >= 0 && dbl <= 2 &&
        ((bplcon3 & 2) || (sprxp >= sprite_minx && sprxp + (16 << dbl) <= sprite_maxx))) {
        ++fast; switch (dbl) {
        case 0: zz_sprite_plain<0>(buf, datab, num); break;
        case 1: zz_sprite_plain<1>(buf, datab, num); break;
        case 2: zz_sprite_plain<2>(buf, datab, num); break;
        }
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
  unsigned cm=rnd()&65535,initial=rnd()&65535;
  clxdat=initial;reference(x,a+16,data,num,dbl,mask,collision,cm);unsigned expected=clxdat;
  clxdat=initial;candidate(x,b+16,data,num,dbl,mask,collision,cm);
  if(expected!=clxdat||memcmp(a,b,sizeof(a))){printf("FAIL %d\n",trial);return 1;}
 }
 printf("PASS 500000 sprite buffer/clipping/collision comparisons; fast spans=%u\n",fast);
}
