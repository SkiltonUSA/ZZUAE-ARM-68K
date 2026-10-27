#include "hotkeys.h"
#include <assert.h>
#include <stdio.h>

int main(void){
    /* Both F10 transitions must reach games unless an Amiga key is held. */
    for(unsigned key=0;key<256;key++){
        assert(!zu_exit_key(key,0));
        assert(!zu_capture_key(key,0));
        assert(!zu_capture_key(key,IEQUALIFIER_CONTROL|IEQUALIFIER_LALT));
        assert(!!zu_capture_key(key,IEQUALIFIER_LCOMMAND)==((key&127)==0x45));
        assert(!!zu_capture_key(key,IEQUALIFIER_RCOMMAND)==((key&127)==0x45));
        assert(!zu_exit_key(key,IEQUALIFIER_CONTROL|IEQUALIFIER_LALT));
        assert(!!zu_exit_key(key,IEQUALIFIER_LCOMMAND)==((key&127)==0x59));
        assert(!!zu_exit_key(key,IEQUALIFIER_RCOMMAND)==((key&127)==0x59));
    }
    puts("PASS: plain Esc/F8/F10 reach guest; Amiga+Esc toggles capture; Amiga+F10 exits");
    return 0;
}
