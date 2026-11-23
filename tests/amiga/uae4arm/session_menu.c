#include "session_menu.h"
#include <assert.h>
#include <stdio.h>
int main(void){
    for(unsigned amiga=0;amiga<2;amiga++){
        unsigned state=0;
        assert(zu_menu_escape(&state,0x45,amiga)==(amiga?ZU_ESC_MENU:ZU_ESC_GUEST));
        /* Amiga may be released before Esc or pressed during a guest Esc. */
        assert(zu_menu_escape(&state,0xc5,!amiga)==(amiga?ZU_ESC_CONSUMED:ZU_ESC_GUEST));
        assert(!state);
    }
    unsigned state=2; /* Key-up was consumed by the modal window. */
    assert(zu_menu_escape(&state,0x45,0)==ZU_ESC_GUEST);
    assert(zu_menu_escape(&state,0xc5,0)==ZU_ESC_GUEST);
    for(unsigned code=0;code<256;code++)if((code&127)!=0x45)
        assert(zu_menu_escape(&state,code,1)==ZU_ESC_OTHER);
    assert(!zu_menu_ready(4,4,0,0));
    assert(!zu_menu_ready(5,4,5,1));
    assert(!zu_menu_ready(5,4,0,1));
    assert(!zu_menu_ready(5,4,5,0));
    assert(zu_menu_ready(5,4,0,0));
    puts("PASS: Escape consumer pairing and unlocked frame-checkpoint gate");
}
