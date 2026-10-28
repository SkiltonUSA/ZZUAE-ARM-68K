#pragma once
#include <stdint.h>
#include <time.h>
/* Host wall-clock fields are used as-is: AmigaOS does not supply a TZ offset. */
static inline int zu_rtc_leap(unsigned year){return year%4==0 && (year%100!=0 || year%400==0);}
static inline void zu_rtc_calendar(uint32_t seconds,struct tm *out){
    static const unsigned char months[]={31,28,31,30,31,30,31,31,30,31,30,31};
    unsigned days=seconds/86400u,year=1970,month=0,span;
    *out=(struct tm){0};out->tm_sec=seconds%60u;out->tm_min=seconds/60u%60u;
    out->tm_hour=seconds/3600u%24u;out->tm_wday=(days+4u)%7u;
    while(days>=(span=365u+zu_rtc_leap(year))){days-=span;++year;}
    out->tm_year=year-1900;out->tm_yday=days;
    while(days>=(span=months[month]+(month==1&&zu_rtc_leap(year)))){days-=span;++month;}
    out->tm_mon=month;out->tm_mday=days+1;
}
