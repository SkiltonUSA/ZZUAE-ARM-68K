/* Host presentation geometry and completed-frame rate; no guest clock changes. */
#pragma once
#include <stdint.h>
#define UL_STATUS_HEIGHT 12u
struct ul_fps {uint32_t start,frames,tenths;};
static inline void ul_fps_start(struct ul_fps *f,uint32_t now){f->start=now;f->frames=f->tenths=0;}
static inline void ul_fps_frame(struct ul_fps *f,uint32_t now){
    uint32_t elapsed=now-f->start;
    ++f->frames;
    if(elapsed>=1000000u){
        f->tenths=(uint32_t)(((uint64_t)f->frames*10000000u+elapsed/2)/elapsed);
        f->start=now;f->frames=0;
    }
}
