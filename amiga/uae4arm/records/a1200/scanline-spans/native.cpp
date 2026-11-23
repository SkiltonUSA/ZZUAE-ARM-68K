#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cassert>
using uae_u32=uint32_t;using uae_u64=uint64_t;
#define STATIC_INLINE static inline
namespace reference {
int toscr_delay[2],toscr_nr_planes2; uint32_t todisplay[8][4],outword[8];
STATIC_INLINE void shift32plus (uae_u32 *p, int n)
{
	uae_u32 t = p[1];
	t <<= n;
	t |= p[0] >> (32 - n);
	p[1] = t;
}

STATIC_INLINE void aga_shift (uae_u32 *p, int n, int fm)
{
	if (fm == 2) {
	  shift32plus (p + 2, n);
	  shift32plus (p + 1, n);
	}
	shift32plus (p + 0, n);
	p[0] <<= n;
}


STATIC_INLINE void toscr_3_aga (int nbits, int fm)
{
	int delay1 = toscr_delay[0];
	int delay2 = toscr_delay[1];
	int i;
	uae_u32 mask = 0xFFFF >> (16 - nbits);

	{
		int offs = (16 << fm) - nbits + delay1;
		int off1 = offs >> 5;
		if (off1 == 3)
			off1 = 2;
		offs -= off1 * 32;
		for (i = 0; i < toscr_nr_planes2; i += 2) {
			uae_u32 t0 = todisplay[i][off1];
			uae_u32 t1 = todisplay[i][off1 + 1];
			uae_u64 t = (((uae_u64)t1) << 32) | t0;
			outword[i] <<= nbits;
			outword[i] |= (t >> offs) & mask;
			aga_shift (todisplay[i], nbits, fm);
		}
	}
	{
		int offs = (16 << fm) - nbits + delay2;
		int off1 = offs >> 5;
		if (off1 == 3)
			off1 = 2;
		offs -= off1 * 32;
		for (i = 1; i < toscr_nr_planes2; i += 2) {
			uae_u32 t0 = todisplay[i][off1];
			uae_u32 t1 = todisplay[i][off1 + 1];
			uae_u64 t = (((uae_u64)t1) << 32) | t0;
			outword[i] <<= nbits;
			outword[i] |= (t >> offs) & mask;
			aga_shift (todisplay[i], nbits, fm);
		}
	}
}

static void toscr_2_2 (int nbits) { toscr_3_aga (nbits, 2); }

}
namespace candidate {
int toscr_delay[2],toscr_nr_planes2; uint32_t todisplay[8][4],outword[8];
STATIC_INLINE void shift32plus (uae_u32 *p, int n)
{
	uae_u32 t = p[1];
	t <<= n;
	t |= p[0] >> (32 - n);
	p[1] = t;
}

STATIC_INLINE void aga_shift (uae_u32 *p, int n, int fm)
{
	if (fm == 2) {
	  shift32plus (p + 2, n);
	  shift32plus (p + 1, n);
	}
	shift32plus (p + 0, n);
	p[0] <<= n;
}


STATIC_INLINE void toscr_3_aga (int nbits, int fm)
{
	int delay1 = toscr_delay[0];
	int delay2 = toscr_delay[1];
	int i;
	uae_u32 mask = 0xFFFF >> (16 - nbits);

	{
		int offs = (16 << fm) - nbits + delay1;
		int off1 = offs >> 5;
		if (off1 == 3)
			off1 = 2;
		offs -= off1 * 32;
		for (i = 0; i < toscr_nr_planes2; i += 2) {
			uae_u32 t0 = todisplay[i][off1];
			uae_u32 t1 = todisplay[i][off1 + 1];
			uae_u64 t = (((uae_u64)t1) << 32) | t0;
			outword[i] <<= nbits;
			outword[i] |= (t >> offs) & mask;
			aga_shift (todisplay[i], nbits, fm);
		}
	}
	{
		int offs = (16 << fm) - nbits + delay2;
		int off1 = offs >> 5;
		if (off1 == 3)
			off1 = 2;
		offs -= off1 * 32;
		for (i = 1; i < toscr_nr_planes2; i += 2) {
			uae_u32 t0 = todisplay[i][off1];
			uae_u32 t1 = todisplay[i][off1 + 1];
			uae_u64 t = (((uae_u64)t1) << 32) | t0;
			outword[i] <<= nbits;
			outword[i] |= (t >> offs) & mask;
			aga_shift (todisplay[i], nbits, fm);
		}
	}
}

static void toscr_2_2 (int nbits) {
    // Specialise the common full span; keep every partial span unchanged.
    if (nbits == 16) toscr_3_aga (16, 2);
    else toscr_3_aga (nbits, 2);
}

}
uint32_t seed=0x87654123;
uint32_t rnd(){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;}
int main(){unsigned long count=0;
for(unsigned trial=0;trial<5000;trial++)for(int planes=0;planes<=8;planes++)for(int n=1;n<=16;n++){
 reference::toscr_nr_planes2=candidate::toscr_nr_planes2=planes;
 for(int d=0;d<2;d++)reference::toscr_delay[d]=candidate::toscr_delay[d]=rnd()%64;
 for(int i=0;i<8;i++){reference::outword[i]=candidate::outword[i]=rnd();for(int j=0;j<4;j++)reference::todisplay[i][j]=candidate::todisplay[i][j]=rnd();}
 reference::toscr_2_2(n);candidate::toscr_2_2(n);
 assert(!memcmp(reference::outword,candidate::outword,sizeof reference::outword));
 assert(!memcmp(reference::todisplay,candidate::todisplay,sizeof reference::todisplay));count++;
}printf("PASS %lu AGA full/partial span and shift-register comparisons\n",count);}
