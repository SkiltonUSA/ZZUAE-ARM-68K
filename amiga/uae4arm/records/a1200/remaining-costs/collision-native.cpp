#include <cstdint>
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
static void reference (void)
{
  int nr_sprites = curr_drawinfo[next_lineno].nr_sprites;
  int first = curr_drawinfo[next_lineno].first_sprite_entry;
  int i;
  unsigned int collision_mask = clxmask[clxcon >> 12];
  int bplres = bplcon0_res;
  hwres_t ddf_left = thisline_decision.plfleft * 2 << bplres;
  hwres_t hw_diwlast = coord_window_to_diw_x (thisline_decision.diwlastword);
  hwres_t hw_diwfirst = coord_window_to_diw_x (thisline_decision.diwfirstword);

  for (i = 0; i < nr_sprites; i++) {
    struct sprite_entry *e = curr_sprite_entries + first + i;
    sprbuf_res_t j;
    sprbuf_res_t minpos = e->pos;
    sprbuf_res_t maxpos = e->max;
    hwres_t minp1 = minpos >> sprite_buffer_res;
    hwres_t maxp1 = maxpos >> sprite_buffer_res;

    if (maxp1 > hw_diwlast)
      maxpos = hw_diwlast << sprite_buffer_res;
    if (maxp1 > thisline_decision.plfright * 2)
      maxpos = thisline_decision.plfright * 2 << sprite_buffer_res;
    if (minp1 < hw_diwfirst)
      minpos = hw_diwfirst << sprite_buffer_res;
    if (minp1 < thisline_decision.plfleft * 2)
      minpos = thisline_decision.plfleft * 2 << sprite_buffer_res;

    for (j = minpos; j < maxpos; j++) {
      int sprpix = spixels[e->first_pixel + j - e->pos] & collision_mask;
      int k, offs, match = 1;

      if (sprpix == 0)
        continue;

      offs = ((j << bplres) >> sprite_buffer_res) - ddf_left;
      sprpix = sprite_ab_merge[sprpix & 255] | (sprite_ab_merge[sprpix >> 8] << 2);
      sprpix <<= 1;

			// both odd and even collision bits already set?
			if ((clxdat & (sprpix << 0)) && (clxdat & (sprpix << 4)))
				continue;

      /* Loop over number of playfields.  */
      for (k = 1; k >= 0; k--) {
        int l;
        int planes = (aga_mode) ? 8 : 6;
        if (bplcon0 & 0x400)
          match = 1;
        for (l = k; match && l < planes; l += 2) {
          int t = 0;
          if (l < thisline_decision.nr_planes) {
            uae_u32 *ldata = (uae_u32 *)(line_data[next_lineno] + 2 * l * MAX_WORDS_PER_LINE);
            ++reads; uae_u32 word = ldata[offs >> 5];
            t = (word >> (31 - (offs & 31))) & 1;
          }
          if (clxcon_bpl_enable & (1 << l)) {
            if (t != ((clxcon_bpl_match >> l) & 1))
              match = 0;
          }
        }
        if (match) {
          clxdat |= sprpix << (k * 4);
        }
      }
    }
  }
}

static void candidate (void)
{
  int nr_sprites = curr_drawinfo[next_lineno].nr_sprites;
  int first = curr_drawinfo[next_lineno].first_sprite_entry;
  int i;
  unsigned int collision_mask = clxmask[clxcon >> 12];
  int bplres = bplcon0_res;
  hwres_t ddf_left = thisline_decision.plfleft * 2 << bplres;
  hwres_t hw_diwlast = coord_window_to_diw_x (thisline_decision.diwlastword);
  hwres_t hw_diwfirst = coord_window_to_diw_x (thisline_decision.diwfirstword);

  for (i = 0; i < nr_sprites; i++) {
    struct sprite_entry *e = curr_sprite_entries + first + i;
    sprbuf_res_t j;
    sprbuf_res_t minpos = e->pos;
    sprbuf_res_t maxpos = e->max;
    hwres_t minp1 = minpos >> sprite_buffer_res;
    hwres_t maxp1 = maxpos >> sprite_buffer_res;

    if (maxp1 > hw_diwlast)
      maxpos = hw_diwlast << sprite_buffer_res;
    if (maxp1 > thisline_decision.plfright * 2)
      maxpos = thisline_decision.plfright * 2 << sprite_buffer_res;
    if (minp1 < hw_diwfirst)
      minpos = hw_diwfirst << sprite_buffer_res;
    if (minp1 < thisline_decision.plfleft * 2)
      minpos = thisline_decision.plfleft * 2 << sprite_buffer_res;

    for (j = minpos; j < maxpos; j++) {
      int sprpix = spixels[e->first_pixel + j - e->pos] & collision_mask;
      int k, offs, match = 1;

      if (sprpix == 0)
        continue;

      offs = ((j << bplres) >> sprite_buffer_res) - ddf_left;
      sprpix = sprite_ab_merge[sprpix & 255] | (sprite_ab_merge[sprpix >> 8] << 2);
      sprpix <<= 1;

			// both odd and even collision bits already set?
			if ((clxdat & (sprpix << 0)) && (clxdat & (sprpix << 4)))
				continue;

      /* Loop over number of playfields.  */
      for (k = 1; k >= 0; k--) {
        int l;
        int planes = (aga_mode) ? 8 : 6;
        if (bplcon0 & 0x400)
          match = 1;
        for (l = k; match && l < planes; l += 2) {
          if (!(clxcon_bpl_enable & (1 << l))) continue;
          int t = 0;
          if (l < thisline_decision.nr_planes) {
            uae_u32 *ldata = (uae_u32 *)(line_data[next_lineno] + 2 * l * MAX_WORDS_PER_LINE);
            ++reads; uae_u32 word = ldata[offs >> 5];
            t = (word >> (31 - (offs & 31))) & 1;
          }
          if (clxcon_bpl_enable & (1 << l)) {
            if (t != ((clxcon_bpl_match >> l) & 1))
              match = 0;
          }
        }
        if (match) {
          clxdat |= sprpix << (k * 4);
        }
      }
    }
  }
}

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
  if(clxdat!=expected){printf("FAIL case=%d expected=%x actual=%x\n",test,expected,clxdat);return 1;}
  if(!clxcon_bpl_enable&&reads){puts("FAIL disabled planes read");return 1;}
 }
 printf("PASS 200000 collision comparisons; private buffer reads reference=%llu candidate=%llu\n",(unsigned long long)before,(unsigned long long)after);
}
