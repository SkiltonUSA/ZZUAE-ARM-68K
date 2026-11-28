#pragma once
/* Escape routing keeps the key-up with the consumer of its key-down. */
enum { ZU_ESC_OTHER, ZU_ESC_GUEST, ZU_ESC_CONSUMED, ZU_ESC_MENU };
static inline unsigned zu_menu_escape(unsigned *state,unsigned code,unsigned amiga){
    if((code&127)!=0x45)return ZU_ESC_OTHER;
    if(code&128){unsigned result=*state==1?ZU_ESC_GUEST:ZU_ESC_CONSUMED;*state=0;return result;}
    *state=amiga?2:1;return amiga?ZU_ESC_MENU:ZU_ESC_GUEST;
}
/* A published, ungranted frame is an existing cooperative checkpoint. */
static inline int zu_menu_ready(unsigned frame,unsigned ack,unsigned active,unsigned locked){
    return frame!=ack && !active && !locked;
}
enum { ZU_MENU_RESUME, ZU_MENU_SCAN, ZU_MENU_CAPTURE, ZU_MENU_EXIT, ZU_MENU_DF0, ZU_MENU_EJECT0, ZU_MENU_DF1, ZU_MENU_EJECT1 };

static inline unsigned zu_menu_entries(unsigned *entries,int testing,int media){
    unsigned n=0;entries[n++]=ZU_MENU_RESUME;
    if(media){entries[n++]=ZU_MENU_DF0;entries[n++]=ZU_MENU_EJECT0;
        entries[n++]=ZU_MENU_DF1;entries[n++]=ZU_MENU_EJECT1;}
    entries[n++]=ZU_MENU_SCAN;if(testing)entries[n++]=ZU_MENU_CAPTURE;
    entries[n++]=ZU_MENU_EXIT;return n;
}
