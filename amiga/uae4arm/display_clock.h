/* GPL-2.0-or-later. Experimental silent presentation planning. */
#pragma once
#include <stdint.h>
struct zu_display_clock { uint32_t rate,period; };
static inline struct zu_display_clock zu_display_clock_plan(uint32_t period,int audio,uint32_t hz){
 uint32_t rate=period?(1000000u+period-1)/period:0;
 if(rate>hz)rate=hz;
 struct zu_display_clock c={rate,(!audio&&rate)?(1000000u+rate-1)/rate:0};return c;
}
