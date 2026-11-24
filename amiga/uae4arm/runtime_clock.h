/* Host calibrates the CPU/2 timer; this never changes the PLL or guest cycles. */
#pragma once
#include <stdint.h>
#include "machine.h"
#define UAE_TIMER_DIVISOR (UAE_OPTIONS+144u)
static inline uint32_t zu_timer_divisor(uint32_t hz){
 if(hz>=320000000u && hz<=345000000u)return 333u;
 if(hz>=396000000u && hz<=404000000u)return 400u;
 return 0;
}
static inline uint64_t zu_timer_us(uint64_t ticks,uint32_t divisor){
 /* Constant division keeps ARMv7's software 64-bit division out of this path.
  * 333 retains existing stock conversion; 400 represents the selected 800 MHz. */
 return divisor==400u?ticks/400u:ticks/333u;
}
