#pragma once
#include <stdint.h>
typedef uae_u32 frame_time_t;
extern int64_t g_uae_epoch;
extern uint64_t zzuae_clock_us(void);
static inline frame_time_t read_processor_time(void){return (frame_time_t)(zzuae_clock_us()-g_uae_epoch);}
static inline int64_t read_processor_time_ns(void){return zzuae_clock_us()*1000;}
