#ifndef ZZUAE_HOTKEYS_H
#define ZZUAE_HOTKEYS_H
#include <devices/inputevent.h>

/* Either Amiga key reserves F10 for the host. Plain F10 belongs to the game. */
static inline int zu_exit_key(unsigned code,unsigned qualifiers){
    return (code&127u)==0x59u &&
        (qualifiers&(IEQUALIFIER_LCOMMAND|IEQUALIFIER_RCOMMAND));
}
static inline int zu_capture_key(unsigned code,unsigned qualifiers){
    return (code&127u)==0x45u &&
        (qualifiers&(IEQUALIFIER_LCOMMAND|IEQUALIFIER_RCOMMAND));
}
#endif
