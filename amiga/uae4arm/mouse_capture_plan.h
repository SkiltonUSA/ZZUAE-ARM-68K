/* One input.device producer, one player consumer; only native host RAM.
 * Main-task reset requires Disable/Enable while the handler is installed. */
#pragma once
#include <stdint.h>
#define UM_CAPACITY 128u
struct um_event {int16_t x,y;uint16_t code;};
struct um_queue {
    volatile uint32_t head,tail,active,overflow;
    struct um_event events[UM_CAPACITY];
};
static inline int um_push(struct um_queue *q,int x,int y,unsigned code){
    uint32_t h=q->head;
    if(h-q->tail==UM_CAPACITY){q->overflow++;q->active=0;return 0;}
    q->events[h%UM_CAPACITY]=(struct um_event){x,y,code};
    __asm__ volatile("" ::: "memory");q->head=h+1;return 1;
}
static inline int um_pop(struct um_queue *q,struct um_event *e){
    uint32_t t=q->tail;if(t==q->head)return 0;
    __asm__ volatile("" ::: "memory");*e=q->events[t%UM_CAPACITY];
    __asm__ volatile("" ::: "memory");q->tail=t+1;return 1;
}
static inline void um_reset(struct um_queue *q){q->active=0;q->tail=q->head;}
