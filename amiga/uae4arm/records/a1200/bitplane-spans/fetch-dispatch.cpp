#include <initializer_list>
#include <cassert>
#include <cstdio>
int plf_state,plf_wait_stop=3,fetch_cycle,fetchstart_mask,fm_maxplane;
int observed,mode_seen,calls;
static const int cycle_sequences[24]={2,1,2,1,2,1,2,1,4,2,3,1,4,2,3,1,8,4,6,2,7,3,5,1};
void fetch(int nr,int fm){observed=nr;mode_seen=fm;++calls;}
void reference(int dma,int fm){
	if (dma && plf_state != plf_wait_stop) {
	  /* fetchstart_mask can be larger than fm_maxplane if FMODE > 0.  This means
	   that the remaining cycles are idle; we'll fall through the whole switch
	   without doing anything.  */
		int cycle_start = fetch_cycle & fetchstart_mask;
		switch (fm_maxplane) {
			case 8:
				switch (cycle_start) {
					case 0: fetch (7, fm); break;
					case 1: fetch (3, fm); break;
					case 2: fetch (5, fm); break;
					case 3: fetch (1, fm); break;
					case 4: fetch (6, fm); break;
					case 5: fetch (2, fm); break;
					case 6: fetch (4, fm); break;
					case 7: fetch (0, fm); break;
				}
				break;
			case 4:
				switch (cycle_start) {
					case 0: fetch (3, fm); break;
					case 1: fetch (1, fm); break;
					case 2: fetch (2, fm); break;
					case 3: fetch (0, fm); break;
				}
				break;
			case 2:
				switch (cycle_start) {
					case 0: fetch (1, fm); break;
					case 1: fetch (0, fm); break;
				}
				break;
		}
	}
}

void candidate(int dma,int fm){
	if (dma && plf_state != plf_wait_stop) {
	  /* fetchstart_mask can be larger than fm_maxplane if FMODE > 0.  This means
	   that the remaining cycles are idle; we'll fall through the whole switch
	   without doing anything.  */
		int cycle_start = fetch_cycle & fetchstart_mask;
        const int *sequence = 0;
        switch (fm_maxplane) {
            case 8: sequence = cycle_sequences + 16; break;
            case 4: sequence = cycle_sequences + 8; break;
            case 2: sequence = cycle_sequences; break;
        }
        if (sequence && cycle_start < fm_maxplane)
            fetch(sequence[cycle_start] - 1, fm);
	}
}

int main(){unsigned cases=0;
for(int fm=0;fm<3;++fm)for(int planes=0;planes<=16;++planes)
for(int mask: {0,1,3,7,15,31})for(int cycle=0;cycle<256;++cycle)
for(int dma=0;dma<2;++dma)for(int state=0;state<6;++state){
 fm_maxplane=planes;fetchstart_mask=mask;fetch_cycle=cycle;plf_state=state;
 observed=-1;mode_seen=-1;calls=0;reference(dma,fm);
 int plane=observed, mode=mode_seen, count=calls;
 observed=-1;mode_seen=-1;calls=0;candidate(dma,fm);
 assert(observed==plane && mode_seen==mode && calls==count);++cases;
}
printf("PASS %u source dispatch comparisons, including idle/reserved modes\n",cases);
}
