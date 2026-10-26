/* GPL-3.0-or-later. Offline emulator installer; adapted from ZZDosBox ZZInstall. */
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/expansion.h>
#include <proto/asl.h>
#include <libraries/asl.h>
#include <devices/ahi.h>
#include <proto/ahi.h>
#include <dos/dosextens.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "averify.h"
struct Library *AHIBase;
struct Library *AslBase;
struct ExpansionBase *ExpansionBase;
static const char version[] __attribute__((used))="$VER: ZZUAEInstall 0.5 (26.10.2026)";

static int library_ok(const char *name, unsigned minimum) {
    struct Library *base=OpenLibrary((STRPTR)name,minimum);
    if(!base){printf("MISSING: %s v%u+\n",name,minimum);return 0;}
    printf("OK: %s %u.%u\n",name,base->lib_Version,base->lib_Revision);
    CloseLibrary(base);return 1;
}
static int audio_ok(void) {
    struct MsgPort *port=CreateMsgPort();struct AHIRequest *req=NULL;
    int ok=0,opened=0;unsigned modes=0;ULONG id=AHI_INVALID_ID;
    if(!port)goto done;
    req=(struct AHIRequest*)CreateIORequest(port,sizeof(*req));if(!req)goto done;
    req->ahir_Version=4;
    if(OpenDevice(AHINAME,AHI_NO_UNIT,(struct IORequest*)req,0))goto done;
    opened=1;AHIBase=(struct Library*)req->ahir_Std.io_Device;
    printf("AHI: device %u.%u\n",AHIBase->lib_Version,AHIBase->lib_Revision);
    while((id=AHI_NextAudioID(id))!=AHI_INVALID_ID)modes++;
    CloseDevice((struct IORequest*)req);opened=0;AHIBase=NULL;
    if(!modes){puts("MISSING: AHI audio modes/drivers");goto done;}
    req->ahir_Version=4;
    if(OpenDevice(AHINAME,0,(struct IORequest*)req,0)){puts("MISSING: configured AHI unit 0");goto done;}
    opened=1;ok=1;printf("OK: %u AHI modes; unit 0 opens (no sound played)\n",modes);
done:
    if(opened)CloseDevice((struct IORequest*)req);
    AHIBase=NULL;if(req)DeleteIORequest((struct IORequest*)req);if(port)DeleteMsgPort(port);
    if(!ok)puts("Install AHI v4+ and an output driver, then configure unit 0 in AHI preferences.");
    return ok;
}
static int dependencies(const char *app) {
    int ok=1;(void)app;
    ok&=library_ok("muimaster.library",19);
    ok&=library_ok("graphics.library",39);
    ok&=library_ok("asl.library",38);
    ok&=library_ok("keymap.library",37);
    ok&=library_ok("Picasso96API.library",2);
    library_ok("lowlevel.library",40); /* Optional physical controller. */
    ExpansionBase=(struct ExpansionBase*)OpenLibrary("expansion.library",0);
    if(ExpansionBase){
        int board=FindConfigDev(NULL,0x6d6e,4)&&FindConfigDev(NULL,0x6d6e,5);
        puts(board?"OK: ZZ9000 graphics and Fast RAM boards":"MISSING: ZZ9000 graphics/Fast RAM boards");
        ok&=board;CloseLibrary((struct Library*)ExpansionBase);ExpansionBase=NULL;
    }else ok=0;
    Forbid();
    { int idle=!FindPort("ZZUAE.Launcher")&&!FindPort("Sixies.ARM.Debug.Owner");Permit();
      if(!idle){puts("Close this emulator launcher and the current Core1 application before installing.");ok=0;}}
    if(!audio_ok())puts("OPTIONAL: choose Paula direct or Sound Off without AHI.");
    puts(ok?"Dependencies passed. Firmware, display modes and available RAM are checked at runtime.":"Dependencies not met; installation stopped. Install the missing components and retry.");
    return ok?0:10;
}
static int join(char *out,size_t cap,const char *base,const char *name){int n=snprintf(out,cap,"%s%s%s",base,(!base[0]||base[strlen(base)-1]==':')?"":"/",name);return n>0&&(size_t)n<cap;}
static int app_ok(const char *name){return !strcmp(name,"ZZUAE");}
static char *read_all(const char *path){FILE*f=fopen(path,"rb");long n;char*b;if(!f)return NULL;fseek(f,0,SEEK_END);n=ftell(f);rewind(f);if(n<0||n>2097152){fclose(f);return NULL;}b=malloc(n+1);if(!b){fclose(f);return NULL;}if(fread(b,1,n,f)!=(size_t)n){free(b);fclose(f);return NULL;}b[n]=0;fclose(f);return b;}
int main(int argc,char **argv){
    if(argc==3&&!strcmp(argv[1],"choose")&&app_ok(argv[2])){
        struct FileRequester *request;char dest[512],title[80];int ok=0;
        snprintf(title,sizeof(title),"Choose parent drawer for %s",argv[2]);
        AslBase=OpenLibrary("asl.library",38);if(!AslBase)return 10;
        request=AllocAslRequestTags(ASL_FileRequest,ASLFR_TitleText,(ULONG)title,ASLFR_DrawersOnly,TRUE,ASLFR_InitialDrawer,(ULONG)"SYS:Programs",TAG_DONE);
        if(request&&AslRequestTags(request,TAG_DONE)&&join(dest,sizeof(dest),(const char*)request->fr_Drawer,argv[2])){printf("\"%s\"\n",dest);ok=1;}
        if(request)FreeAslRequest(request);CloseLibrary(AslBase);return ok?0:10;
    }
    if(argc==3&&!strcmp(argv[1],"check")&&app_ok(argv[2]))return dependencies(argv[2]);
    if(argc==5&&!strcmp(argv[1],"verify")){
        char *catalog=read_all(argv[2]),*sig=read_all(argv[3]),*key=read_all(argv[4]);int ok=0;
        if(catalog&&sig&&key){key[strcspn(key,"\r\n")]=0;sig[strcspn(sig,"\r\n")]=0;ok=amipkg_verify_index_key((unsigned char*)catalog,strlen(catalog),sig,key);}
        free(catalog);free(sig);free(key);puts(ok?"Catalogue signature verified.":"Invalid catalogue signature; installation stopped.");return ok?0:10;
    }
    puts("ZZUAEInstall check|choose ZZUAE / verify catalogue signature public-key");return 10;
}
