#include "disk_swap.h"
extern "C" unsigned zzuae_disk_command(unsigned,unsigned);
static unsigned media_sequence;
static void media_command(){
    ad_put(uae_shared,UM_CAPS,UM_MAGIC);barrier();
    unsigned sequence=ad_get(uae_shared,UM_REQUEST);
    if(sequence==media_sequence)return;
    barrier();
    unsigned result=zzuae_disk_command(ad_get(uae_shared,UM_OPERATION),ad_get(uae_shared,UM_UNIT));
    ad_put(uae_shared,UM_RESULT,result);barrier();
    media_sequence=sequence;ad_put(uae_shared,UM_REPLY,sequence);barrier();
}
