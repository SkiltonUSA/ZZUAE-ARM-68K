#include "runtime_clock.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 assert(zu_timer_divisor(333333333)==333);
 assert(zu_timer_divisor(399999690)==400);
 assert(zu_timer_divisor(320000000)==333 && zu_timer_divisor(345000000)==333);
 assert(zu_timer_divisor(396000000)==400 && zu_timer_divisor(404000000)==400);
 assert(!zu_timer_divisor(0) && !zu_timer_divisor(350000000) && !zu_timer_divisor(450000000));
 assert(zu_timer_us(4000000000ull,400)==10000000ull);
 assert(zu_timer_us(3330000000ull,333)==10000000ull);
 assert(zu_timer_us(4000000000ull,400)-zu_timer_us(3600000000ull,400)==1000000ull);
 assert(zu_timer_us(400ull*86400*1000000,400)==86400ull*1000000);
 assert(UAE_TIMER_DIVISOR>=UAE_OPTIONS+144 && UAE_TIMER_DIVISOR+4<=0x482900);
 puts("PASS stock/800 MHz calibration, rejection, microseconds, long uptime and control bounds");
}
