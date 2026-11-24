"""Publish calibrated host-clock scaling before the guest starts."""
def host_clock(text):
    old='if(rate<320000000u || rate>345000000u)goto done;'
    if old not in text:
        if 'UAE_TIMER_DIVISOR' in text:return text
        raise ValueError('Unrecognised clock gate')
    assert text.count(old)==1
    return '#include "runtime_clock.h"\n'+text.replace(old,'''
    {ULONG divisor=zu_timer_divisor(rate);
     if(!divisor){printf("ERROR Unsupported ARM timer rate %u Hz\\n",rate);goto done;}
     ad_put(shared,UAE_TIMER_DIVISOR,divisor);
     syncio->push(shared+UAE_TIMER_DIVISOR,4,NULL);syncio->barrier(NULL);
     printf("STARTUP ARM timer: %u ticks/us\\n",divisor);}
''')
