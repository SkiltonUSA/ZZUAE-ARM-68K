/* Upstream produces 256-frame chunks; batch four before crossing to 68K. */
#include "audio_wire.h"
#include "protocol.h"
#include "gensound.h"
#include "profile.h"
static unsigned pcm_frames,pcm_write,pcm_nonzero;
static uint8_t pcm[UA_STRIDE];
static void pcm_publish(void) {
    ZU_PROFILE(3);
    volatile uint8_t *p=uae_shared;
    while(!ua_room(pcm_write,ad_get(p,UA_READ)))
        if(uae_stop && uae_stop()){pcm_frames=0;return;}
    __asm__ volatile("dsb sy" ::: "memory");
    memcpy((void*)(p+UA_DATA+(pcm_write%UA_SLOTS)*UA_STRIDE),pcm,sizeof(pcm));
    ad_put(p,UA_NONZERO,pcm_nonzero);
    __asm__ volatile("dsb sy" ::: "memory");
    ad_put(p,UA_WRITE,++pcm_write);
    __asm__ volatile("dsb sy" ::: "memory");pcm_frames=0;
}
void finish_sound_buffer(){
    if(uae_shared && (ad_get(uae_shared,UAE_OPTIONS+4)&UAE_OPT_AUDIO)) {
        unsigned n=(sndbufpt-sndbuffer[0])/2;
        for(unsigned i=0;i<n;i++){
            /* UAE's first pair is channels 0+3 (physical right). */
            uint16_t left=sndbuffer[0][2*i+1],right=sndbuffer[0][2*i];
            ua_pcm(pcm+pcm_frames*4,left,right);
            if(left||right)pcm_nonzero++;
            if(++pcm_frames==UA_FRAMES)pcm_publish();
        }
    }
    restart_sound_buffer();
}
void update_sound(float clk){
    if(currprefs.sound_freq)scaled_sample_evtime=(uae_u32)(clk*CYCLE_UNIT/currprefs.sound_freq);
}
