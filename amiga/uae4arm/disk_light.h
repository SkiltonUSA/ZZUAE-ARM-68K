#pragma once
#include <stdint.h>
/* Coalesce read bursts into visible pulses; never blink from motor state alone. */
struct zu_disk_light { uint32_t seen,changed,read_at;unsigned on,pending; };
static inline int zu_disk_light_update(struct zu_disk_light *s,uint32_t reads,uint32_t now,int running){
    if(!running){s->seen=reads;s->on=s->pending=0;s->changed=now;return 0;}
    if(reads!=s->seen){s->seen=reads;s->read_at=now;s->pending=1;}
    if((uint32_t)(now-s->read_at)>=120000u)s->pending=0;
    if(s->on){
        if((uint32_t)(now-s->changed)>=60000u){s->on=0;s->changed=now;}
    }else if(s->pending && (uint32_t)(now-s->changed)>=40000u){
        s->on=1;s->pending=0;s->changed=now;
    }
    return s->on;
}
