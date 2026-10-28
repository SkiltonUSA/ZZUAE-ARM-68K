#include <assert.h>
#include <stdio.h>
#include "rtc_time.h"
static void check(uint32_t seconds,int year,int month,int day,int h,int m,int s,int weekday,int yearday){
 struct tm t;zu_rtc_calendar(seconds,&t);
 assert(t.tm_year==year-1900&&t.tm_mon==month-1&&t.tm_mday==day);
 assert(t.tm_hour==h&&t.tm_min==m&&t.tm_sec==s);
 assert(t.tm_wday==weekday&&t.tm_yday==yearday&&t.tm_isdst==0);
}
int main(void){
 check(0,1970,1,1,0,0,0,4,0);
 check(951827696,2000,2,29,12,34,56,2,59);
 check(1793188800,2026,10,28,12,0,0,3,300);
 check(2147483647,2038,1,19,3,14,7,2,18);
 check(4107542400u,2100,3,1,0,0,0,1,59);
 puts("PASS RTC calendar: epoch, leap day, host date, 2038 and non-leap century");
}
