#pragma once
#include <stdint.h>
/* Unsigned subtraction also handles the microsecond clock wrapping. */
static inline int zu_frame_due(uint32_t now,uint32_t last,uint32_t period) {
    return (uint32_t)(now-last)>=period;
}
static inline uint32_t zu_run_timeout(uint32_t frames,uint32_t period) {
    /* Callers restrict frames to 6000 and period to at most 40000 us. */
    uint32_t planned=frames*period+30000000u;
    return planned>120000000u?planned:120000000u;
}
