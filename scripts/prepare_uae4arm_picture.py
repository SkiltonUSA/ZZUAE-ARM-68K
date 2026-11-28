"""Add a bounded guest-picture offset to the host interface."""
def host_picture(text):
    if 'static unsigned picture_up;' in text:return text
    marker='else if(!strcmp(argv[i],"RTC") && i+1<argc)'
    assert marker in text
    text=text.replace(marker,'''else if(!strcmp(argv[i],"PICTUREUP") && i+1<argc){
        char *end;unsigned long n=strtoul(argv[++i],&end,10);
        if(!*argv[i]||*end||n>24){puts("ERROR PICTUREUP must be 0..24 lines");return 20;}
        picture_up=n;
    }
    '''+marker)
    marker='ad_put(shared,UAE_RTC_ENABLE,rtc_mode);'
    assert marker in text
    text=text.replace(marker,'''ad_put(shared,UAE_PICTURE_UP,picture_up);
    syncio->push(shared+UAE_PICTURE_UP,4,NULL);syncio->barrier(NULL);
    printf("STARTUP Picture shift: %u lines up\\n",picture_up);
    '''+marker)
    return '#include "picture_position.h"\n#ifdef UAE_BOOT\nstatic unsigned picture_up;\n#endif\n'+text
