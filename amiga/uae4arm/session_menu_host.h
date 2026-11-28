/* Native menu while Core1 waits on UL_GRANT/UL_ACK. No bitmap is locked,
 * no core state is rewritten, and the existing stop/teardown path is retained. */
static void live_menu_paint(struct Window *w,struct DrawInfo *d,unsigned selected,int confirm,int row,int media){
    struct RastPort *rp=w->RPort;
    unsigned entries[8];
    unsigned count=zu_menu_entries(entries,frame_limit!=0,media);
    if(confirm)count=2;
    SetFont(rp,d->dri_Font);SetDrMd(rp,JAM1);
    SetAPen(rp,d->dri_Pens[BACKGROUNDPEN]);
    RectFill(rp,w->BorderLeft,w->BorderTop,w->Width-w->BorderRight-1,w->Height-w->BorderBottom-1);
    for(unsigned i=0;i<count;i++){
        char text[512];int top=w->BorderTop+4+i*row;
        if(confirm)snprintf(text,sizeof text,"%s",i?"Exit emulator":"Cancel");
        else switch(entries[i]){
#ifdef ZZUAE_DISK_SWAP
        case ZU_MENU_DF0:case ZU_MENU_DF1:{
            unsigned unit=entries[i]==ZU_MENU_DF1;const char *path=us_disk_name(unit);
            snprintf(text,sizeof text,"DF%u: %s",unit,*path?(char *)FilePart((STRPTR)path):"Empty - insert...");break;
        }
        case ZU_MENU_EJECT0:snprintf(text,sizeof text,"Eject DF0");break;
        case ZU_MENU_EJECT1:snprintf(text,sizeof text,"Eject DF1");break;
#endif
        case ZU_MENU_RESUME:snprintf(text,sizeof text,"Resume");break;
        case ZU_MENU_SCAN:snprintf(text,sizeof text,"Scanlines: %s",live_scan.regs?zu_scan_names[live_scan.mode]:"fullscreen only");break;
        case ZU_MENU_CAPTURE:snprintf(text,sizeof text,"Screenshot");break;
        default:snprintf(text,sizeof text,"Exit emulator");break;
        }
        SetAPen(rp,d->dri_Pens[i==selected?FILLPEN:BACKGROUNDPEN]);
        RectFill(rp,w->BorderLeft+4,top,w->Width-w->BorderRight-5,top+row-2);
        SetAPen(rp,d->dri_Pens[i==selected?FILLTEXTPEN:TEXTPEN]);
        unsigned length=strlen(text);while(length&&TextLength(rp,text,length)>w->Width-w->BorderLeft-w->BorderRight-16)length--;
        Move(rp,w->BorderLeft+8,top+(row-rp->TxHeight)/2+rp->TxBaseline);Text(rp,text,length);
    }
}
static void live_session_menu(void){
    ULONG started=us();struct IntuiMessage *m;
    live_mouse_release(1);ClearPointer(live_window);
    live_keys=live_stick=live_joy_sent=0;live_input(UL_RESET_INPUT,0);
    if(!ua_audio_host_pause_drain()){puts("ERROR Menu audio drain timed out");live_abort();return;}
    struct DrawInfo *d=GetScreenDrawInfo(live_screen);
    if(!d){live_abort();return;}
    int media=0;
#ifdef ZZUAE_DISK_SWAP
    media=live_media_available();
#endif
    unsigned entries[8];
    int row=d->dri_Font->tf_YSize+8,width=300,count=zu_menu_entries(entries,frame_limit!=0,media);
    if(width>live_screen->Width-16)width=live_screen->Width-16;
    struct Window *w=OpenWindowTags(NULL,WA_CustomScreen,(ULONG)live_screen,
        WA_Title,(ULONG)"ZZUAE - Paused",WA_InnerWidth,width,WA_InnerHeight,count*row+8,
        WA_Left,live_window->LeftEdge+(live_window->Width-width)/2,
        WA_Top,live_window->TopEdge+(live_window->Height-count*row-8)/2,WA_AutoAdjust,TRUE,WA_DragBar,TRUE,
        WA_CloseGadget,TRUE,WA_Activate,TRUE,WA_RMBTrap,TRUE,WA_SimpleRefresh,TRUE,
        WA_IDCMP,IDCMP_RAWKEY|IDCMP_MOUSEBUTTONS|IDCMP_CLOSEWINDOW|IDCMP_REFRESHWINDOW,TAG_DONE);
    if(w){
        unsigned selected=0;int done=0,confirm=0;
        puts("STARTUP Paused: Amiga+Esc menu");
        live_menu_paint(w,d,selected,confirm,row,media);
        WindowToFront(w);ActivateWindow(w);
        while(!done){
            ULONG signals=Wait((1UL<<w->UserPort->mp_SigBit)|SIGBREAKF_CTRL_C);
            if(signals&SIGBREAKF_CTRL_C){live_stop();done=1;}
            while((m=(struct IntuiMessage*)GetMsg(w->UserPort))){
                ULONG cl=m->Class;UWORD code=m->Code,qual=m->Qualifier;
                int x=m->MouseX,y=m->MouseY,activate=0;ReplyMsg((struct Message*)m);
                if(done)continue;
                if(cl==IDCMP_CLOSEWINDOW)done=1;
                else if(cl==IDCMP_RAWKEY && !(code&128) && !(qual&IEQUALIFIER_REPEAT)){
                    if(code==0x45)done=1;
                    else if(zu_exit_key(code,qual)){live_stop();done=1;}
                    else if(code==0x4c)selected=selected?selected-1:(unsigned)count-1;
                    else if(code==0x4d)selected=(selected+1)%count;
                    else if(code==0x44||code==0x43||code==0x40)activate=1;
                }else if(cl==IDCMP_MOUSEBUTTONS && code==SELECTUP){
                    int y0=y-w->BorderTop-4;
                    if(y0>=0 && y0<count*row && x>=w->BorderLeft+4 && x<w->Width-w->BorderRight-4){selected=y0/row;activate=1;}
                }else if(cl==IDCMP_REFRESHWINDOW){BeginRefresh(w);live_menu_paint(w,d,selected,confirm,row,media);EndRefresh(w,TRUE);}
                if(activate){
                    if(confirm){if(selected)live_stop();done=1;}
                    else if(entries[selected]==ZU_MENU_RESUME)done=1;
                    else if(entries[selected]==ZU_MENU_SCAN){
                        if(live_scan.regs){zu_scan_next(&live_scan);printf("STARTUP ZZScanlines firmware: %s\n",zu_scan_names[live_scan.mode]);}
                    }else if(entries[selected]==ZU_MENU_CAPTURE){live_capture_pending=1;done=1;}
#ifdef ZZUAE_DISK_SWAP
                    else if(entries[selected]>=ZU_MENU_DF0){
                        unsigned item=entries[selected];
                        live_media_select(w,item>=ZU_MENU_DF1,item==ZU_MENU_EJECT0||item==ZU_MENU_EJECT1);
                        if(live_quit)done=1;else ActivateWindow(w);
                    }
#endif
                    else{confirm=1;selected=0;count=2;SetWindowTitles(w,(STRPTR)"Exit emulator?",(STRPTR)-1);}
                }
                if(!done)live_menu_paint(w,d,selected,confirm,row,media);
            }
        }
        CloseWindow(w);
    }else{puts("ERROR Cannot open session menu");live_abort();}
    FreeScreenDrawInfo(live_screen,d);
    /* Discard focus/key messages accumulated while paused. A key released in
     * the modal window must not stay held in the guest after Resume. */
    while((m=(struct IntuiMessage*)GetMsg(live_window->UserPort)))ReplyMsg((struct Message*)m);
    live_escape_state=2;live_input(UL_RESET_INPUT,0);
    ULONG elapsed=us()-started;live_paused_us+=elapsed;live_started+=elapsed;live_last=us();
    ul_fps_start(&live_fps,live_last);
    if(!live_quit){
        live_focused=1;WindowToFront(live_window);ActivateWindow(live_window);
        if(fullscreen_mode)SetPointer(live_window,live_pointer,1,16,0,0);
        puts("STARTUP Resumed");
    }
}
