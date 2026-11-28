#pragma once
#include <libraries/asl.h>
#include <proto/asl.h>
struct Library *AslBase;
static unsigned media_sequence;
static unsigned live_media_request(unsigned operation,unsigned unit){
    unsigned sequence=++media_sequence;
    ad_put(shared,UM_OPERATION,operation);ad_put(shared,UM_UNIT,unit);
    syncio->push(shared+UM_OPERATION,8,NULL);syncio->barrier(NULL);
    ad_put(shared,UM_REQUEST,sequence);syncio->push(shared+UM_REQUEST,4,NULL);syncio->barrier(NULL);
    ULONG started=us();
    while(us()-started<2000000u){
        if(!us_host_service()){live_abort();return 0;}
        syncio->pull(shared+UM_REPLY,8,NULL);
        if(ad_get(shared,UM_REPLY)==sequence)return ad_get(shared,UM_RESULT);
        Delay(1);
    }
    puts("ERROR Disk command timed out; stopping emulator");live_abort();return 0;
}
static int live_media_available(void){
    syncio->pull(shared+UM_CAPS,4,NULL);
    return ad_get(shared,UM_CAPS)==UM_MAGIC;
}
static void live_media_error(struct Window *window){
    if(live_quit)return;
    struct EasyStruct error={sizeof(struct EasyStruct),0,
        (STRPTR)"Disk unchanged",(STRPTR)"Image unavailable, already in use, or drive busy.\nCheck the file or resume and retry.",(STRPTR)"OK"};
    EasyRequestArgs(window,&error,NULL,NULL);
}
static void live_media_select(struct Window *window,unsigned unit,int eject){
    if(eject){if(!us_swap_disk(unit,""))live_media_error(window);return;}
    AslBase=OpenLibrary("asl.library",38);
    if(!AslBase){puts("ERROR Disk selection needs asl.library V38");return;}
    char drawer[512],path[512];const char *current=us_disk_name(unit);
    snprintf(drawer,sizeof drawer,"%s",*current?current:*disk_path?disk_path:"PROGDIR:Disks/");
    char *part=(char *)FilePart(drawer);*part=0;
    struct FileRequester *r=AllocAslRequestTags(ASL_FileRequest,
        ASLFR_Window,(ULONG)window,ASLFR_TitleText,(ULONG)(unit?"Insert DF1 disk":"Insert DF0 disk"),
        ASLFR_InitialDrawer,(ULONG)drawer,ASLFR_InitialPattern,(ULONG)"#?.adf",
        ASLFR_DoPatterns,TRUE,ASLFR_RejectIcons,TRUE,TAG_DONE);
    if(r){
        if(AslRequestTags(r,TAG_DONE)){
            int length=snprintf(path,sizeof path,"%s",r->fr_Drawer);
            if(length>=0 && (unsigned)length<sizeof path && AddPart(path,r->fr_File,sizeof path)){
                printf("MEDIA DF%u requested: %s\n",unit,path);
                if(!us_swap_disk(unit,path))live_media_error(window);
            }
            else puts("ERROR Disk path is too long");
        }
        FreeAslRequest(r);
    }
    CloseLibrary(AslBase);AslBase=NULL;
}
