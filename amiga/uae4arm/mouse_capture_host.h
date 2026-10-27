/* Window capture: input.device delivers relative mouse reports while the
 * native pointer remains parked. No ARM/Intuition calls from the handler. */
#include <devices/input.h>
#include <exec/interrupts.h>
#include "mouse_capture_plan.h"
static struct um_queue live_mouse_queue;
static struct MsgPort *live_mouse_port;
static struct IOStdReq *live_mouse_io;
static struct Interrupt live_mouse_handler;
static int live_mouse_opened,live_mouse_installed,live_mouse_hidden,live_mouse_pending;
static void live_input(unsigned,int);

struct InputEvent *zu_mouse_handler(struct InputEvent *events){
    struct InputEvent *e;
    if(IntuitionBase->ActiveWindow!=live_window)live_mouse_queue.active=0;
    for(e=events;e;e=e->ie_NextEvent){
        /* The escape route works even while the main task awaits an ARM frame. */
        if(e->ie_Class==IECLASS_RAWKEY && (e->ie_Code==0x57 || e->ie_Code==0x59))
            live_mouse_queue.active=0;
        if(live_mouse_queue.active && e->ie_Class==IECLASS_RAWMOUSE){
            um_push(&live_mouse_queue,e->ie_X,e->ie_Y,e->ie_Code);
            e->ie_Class=IECLASS_NULL;
        }
    }
    return events;
}
extern void zu_mouse_entry(void);
__asm__(".text\n.globl _zu_mouse_entry\n_zu_mouse_entry:\n"
 "movem.l %d1-%d7/%a0-%a6,-(%sp)\nmove.l %a0,-(%sp)\n"
 "jsr _zu_mouse_handler\naddq.l #4,%sp\n"
 "movem.l (%sp)+,%d1-%d7/%a0-%a6\nrts\n");

static void live_mouse_title(int captured){
    snprintf(live_title,sizeof(live_title),"ZZUAE - %s - %s / F10 exit",
        profile==0?"A1000":profile==2?"A500 Plus":profile==3?"A600":"A500",
        captured?"F8 release mouse":"Click to capture mouse");
    SetWindowTitles(live_window,live_title,(STRPTR)-1);
}
static void live_mouse_release(int send_release){
    Disable();um_reset(&live_mouse_queue);Enable();live_mouse_pending=0;
    if(live_mouse_hidden){
        ClearPointer(live_window);live_mouse_hidden=0;
        if(send_release){live_input(UL_LEFT,0);live_input(UL_RIGHT,0);}
        live_mouse_title(0);
        puts("MOUSE released");
    }
}
static void live_mouse_capture(void){
    if(!live_focused)return;
    Disable();um_reset(&live_mouse_queue);live_mouse_queue.active=1;Enable();
    SetPointer(live_window,live_pointer,1,16,0,0);live_mouse_hidden=1;
    live_mouse_title(1);puts("MOUSE captured; F8 releases to Workbench");
}
static int live_mouse_open(void){
    live_mouse_port=CreateMsgPort();if(!live_mouse_port)return 0;
    live_mouse_io=(struct IOStdReq*)CreateIORequest(live_mouse_port,sizeof(*live_mouse_io));
    if(!live_mouse_io || OpenDevice("input.device",0,(struct IORequest*)live_mouse_io,0))return 0;
    live_mouse_opened=1;
    live_mouse_handler.is_Node.ln_Type=NT_INTERRUPT;
    live_mouse_handler.is_Node.ln_Pri=60;
    live_mouse_handler.is_Node.ln_Name="ZZUAE mouse capture";
    live_mouse_handler.is_Code=(void*)zu_mouse_entry;
    live_mouse_io->io_Data=&live_mouse_handler;live_mouse_io->io_Command=IND_ADDHANDLER;
    if(DoIO((struct IORequest*)live_mouse_io))return 0;
    live_mouse_installed=1;live_mouse_title(0);return 1;
}
static void live_mouse_close(void){
    if(live_mouse_installed){
        live_mouse_release(0);
        live_mouse_io->io_Command=IND_REMHANDLER;
        DoIO((struct IORequest*)live_mouse_io);live_mouse_installed=0;
        printf("MOUSE cleanup: handler removed; overflow=%u\n",(unsigned)live_mouse_queue.overflow);
    }
    if(live_mouse_opened){CloseDevice((struct IORequest*)live_mouse_io);live_mouse_opened=0;}
    if(live_mouse_io){DeleteIORequest((struct IORequest*)live_mouse_io);live_mouse_io=NULL;}
    if(live_mouse_port){DeleteMsgPort(live_mouse_port);live_mouse_port=NULL;}
}
static void live_mouse_drain(void){
    struct um_event e;
    if(!live_mouse_queue.active){if(live_mouse_hidden)live_mouse_release(1);return;}
    if(live_mouse_queue.head==live_mouse_queue.tail)return;
    volatile uint8_t *p=shared+UAE_LIVE;
    syncio->pull(p+UL_TAIL,4,NULL);
    ULONG tail=ad_get(p,UL_TAIL);
    /* Reserve room for both axes and a button; retain queued events if the
     * guest ring is busy instead of turning a motion burst into an abort. */
    while(ad_get(p,UL_HEAD)-tail<=UL_CAPACITY-3 && um_pop(&live_mouse_queue,&e)){
        if(e.x)live_input(UL_MOUSE_X,e.x);
        if(e.y)live_input(UL_MOUSE_Y,e.y);
        if(e.code==SELECTDOWN || e.code==SELECTUP)live_input(UL_LEFT,e.code==SELECTDOWN);
        if(e.code==MENUDOWN || e.code==MENUUP)live_input(UL_RIGHT,e.code==MENUDOWN);
    }
}
static void live_mouse_click(UWORD code){
    int x=live_window->MouseX-live_window->BorderLeft,y=live_window->MouseY-live_window->BorderTop;
    int inside=x>=0 && y>=0 && (unsigned)x<live_width && (unsigned)y<live_height;
    if(code==SELECTDOWN)live_mouse_pending=inside;
    if(code==SELECTUP){
        int capture=live_mouse_pending&&inside;live_mouse_pending=0;
        if(capture)live_mouse_capture(); /* swallow the activating click */
    }
}
