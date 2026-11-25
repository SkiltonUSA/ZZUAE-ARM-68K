"""Apply display-only cadence to the sound-off host path."""
def host_cadence(text):
    include='#include "display_clock.h"\n'
    if include in text:
        return text
    marker='        if(audio_mode){\n            if(!(boot_options&UAE_OPT_LIVE))return 20;'
    if text.count(marker)!=1:
        raise ValueError('Unrecognised host audio setup')
    return include+text.replace(marker,'''        if(!audio_mode){
            struct zu_display_clock clock=zu_display_clock_plan(frame_period,0,ntsc_mode?60:50);
            display_rate=clock.rate;frame_period=clock.period;
        }
'''+marker)
