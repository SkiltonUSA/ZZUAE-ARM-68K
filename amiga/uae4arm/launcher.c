/* Native MUI launcher. ARM execution remains in the separate player process. */
#include <libraries/mui.h>
#include <libraries/asl.h>
#include <libraries/configvars.h>
#include <workbench/workbench.h>
#include <devices/timer.h>
#include <dos/dostags.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/intuition.h>
#include <proto/muimaster.h>
#include <proto/asl.h>
#include <proto/expansion.h>
#include <proto/icon.h>
#include <clib/alib_protos.h>
#include "launcher_config.h"
#include "disk_check.h"
#pragma GCC diagnostic ignored "-Wpointer-sign"
struct Library *MUIMasterBase,*AslBase,*IconBase;
struct ExpansionBase *ExpansionBase;
static Object *app,*win,*loglist,*settings,*romfield,*diskfield,*output,*renderer,*writes,*limit,*fps,*ram,*machine,*sound,*joystick,*scanlines,*chipset,*status,*start,*save,*cancel;
static struct zu_config config;
static char appdir[ZU_PATH],player[ZU_PATH],cfgpath[ZU_PATH],logpath[ZU_PATH];
static char session[16],stopname[48],command[4096],partial[768];
static unsigned partial_size,loglines,serial;
static LONG logoffset;
static int busy,closing,stop_requested,stop_sent,timer_pending,timer_open;
/* Ctrl-C is handled by the event loop, including child cleanup. */
void __chkabort(void){}
static struct MsgPort *doneport,*timerport,*uiport;
static struct timerequest *timer;
static const char ver[]="$VER: ZZUAE " ZU_VERSION " (26.10.2026)";
static const char *outputs[]={"Workbench window","Capture only",NULL};
static const char *renderers[]={"Direct ARM bitmap","CPU copy (test)",NULL};
static const char *write_modes[]={"Read only","Temporary writes",NULL};
static const char *machines[]={"A1000","A500","A500 Plus","A600",NULL};
static const char *mem1000[]={"256K Chip","512K Chip",NULL};
static const char *mem500[]={"512K Chip","512K Chip + 512K Slow",NULL};
static const char *memecs[]={"1 MB Chip","2 MB Chip",NULL};
static const char **memory_entries(unsigned p){return p==0?mem1000:p==1?mem500:memecs;}
static const char *rates[]={"25 FPS","30 FPS","MAX FPS","50 FPS",NULL};
static const char *joy_modes[]={"Off","Amiga port 2",NULL};
static const char *scan_modes[]={"Off","Soft","Smooth","Hard",NULL};
static const char *sounds[]={"Off","Paula direct","AHI",NULL};
static const char *limits[]={"500 frames","1000 frames","1800 frames","3000 frames",NULL};
enum {ID_START=1,ID_SAVE,ID_ROM,ID_DISK,ID_OUTPUT,ID_MACHINE,ID_JOY,ID_JOY_CLOSE,ID_SCANLINES};
struct job {struct Message done;LONG result;BPTR log;} ;
static struct job job;

static ULONG val(Object *o,ULONG attr){ULONG v=0;get(o,attr,&v);return v;}
static Object *label(const char *s){return TextObject,MUIA_Text_PreParse,(ULONG)"\33r",MUIA_Text_Contents,(ULONG)s,End;}
static Object *readout(const char *s){return TextObject,TextFrame,MUIA_Text_PreParse,(ULONG)"\33c",MUIA_Text_Contents,(ULONG)s,End;}
static Object *cycle(const char **entries){return CycleObject,MUIA_CycleChain,1,MUIA_Cycle_Entries,(ULONG)entries,End;}
static Object *field(void){return StringObject,StringFrame,MUIA_CycleChain,1,MUIA_String_MaxLen,ZU_PATH,End;}
static void note(const char *s){
    if(loglines>=200){DoMethod(loglist,MUIM_List_Remove,MUIV_List_Remove_First);loglines--;}
    DoMethod(loglist,MUIM_List_InsertSingle,(ULONG)s,MUIV_List_Insert_Bottom);loglines++;
    set(loglist,MUIA_List_Active,MUIV_List_Active_Bottom);
}
static void state(const char *s){set(status,MUIA_Text_Contents,(ULONG)s);}
static int path(char *dst,const char *name){strcpy(dst,appdir);return AddPart(dst,(STRPTR)name,ZU_PATH);}
static void notify(Object *o,ULONG attr,ULONG value,ULONG id){DoMethod(o,MUIM_Notify,attr,value,(ULONG)app,2,MUIM_Application_ReturnID,id);}
#include "joystick_ui.h"
#include "splash.h"
static void controls(void){
    set(settings,MUIA_Disabled,busy);set(save,MUIA_Disabled,busy);set(start,MUIA_Disabled,busy);
    set(renderer,MUIA_Disabled,busy||val(output,MUIA_Cycle_Active));
    set(sound,MUIA_Disabled,busy||val(output,MUIA_Cycle_Active));
    set(fps,MUIA_Disabled,busy||val(output,MUIA_Cycle_Active));
    set(scanlines,MUIA_Disabled,busy||val(output,MUIA_Cycle_Active));
    set(cancel,MUIA_Text_Contents,(ULONG)(busy?"Stop":"Cancel"));
}
static void read_config(void){
    snprintf(config.rom,sizeof(config.rom),"%s",(char*)val(romfield,MUIA_String_Contents));
    snprintf(config.disk,sizeof(config.disk),"%s",(char*)val(diskfield,MUIA_String_Contents));
    config.output=val(output,MUIA_Cycle_Active);config.renderer=val(renderer,MUIA_Cycle_Active);
    config.writes=val(writes,MUIA_Cycle_Active);config.limit=val(limit,MUIA_Cycle_Active);config.fps=val(fps,MUIA_Cycle_Active);config.ram=val(ram,MUIA_Cycle_Active);
    config.audio=val(sound,MUIA_Cycle_Active);config.joystick=val(joystick,MUIA_Cycle_Active);config.scanlines=val(scanlines,MUIA_Cycle_Active);
    strcpy(config.roms[config.profile],config.rom);
}
static void select_machine(void){
    unsigned next=val(machine,MUIA_Cycle_Active);
    if(next==config.profile)return;
    read_config();config.profile=next;config.ram=next==0?1:0;
    strcpy(config.rom,config.roms[next]);
    set(ram,MUIA_Cycle_Entries,(ULONG)memory_entries(next));set(ram,MUIA_Cycle_Active,config.ram);
    set(chipset,MUIA_Text_Contents,(ULONG)(next<2?"OCS / PAL":"ECS / PAL"));
    set(romfield,MUIA_String_Contents,(ULONG)config.rom);
    state("Machine settings applied");
}
static void browse(Object *field,const char *title){
    struct FileRequester *r;char selected[ZU_PATH];
    snprintf(selected,sizeof(selected),"%s",(char*)val(field,MUIA_String_Contents));
    *FilePart(selected)=0;
    set(app,MUIA_Application_Sleep,TRUE);
    r=AllocAslRequestTags(ASL_FileRequest,ASLFR_TitleText,(ULONG)title,ASLFR_InitialDrawer,(ULONG)selected,TAG_DONE);
    if(r){
        if(AslRequestTags(r,TAG_DONE) && strlen(r->fr_Drawer)<sizeof(selected)){
            strcpy(selected,r->fr_Drawer);
            if(AddPart(selected,r->fr_File,sizeof(selected)))set(field,MUIA_String_Contents,(ULONG)selected);
        }
        FreeAslRequest(r);
    }
    set(app,MUIA_Application_Sleep,FALSE);
}
static int file_size(const char *name,LONG expected){
    struct FileInfoBlock *fib=AllocDosObject(DOS_FIB,NULL);BPTR lock;int ok=0;
    if(!fib)return 0;
    lock=Lock((STRPTR)name,ACCESS_READ);
    if(lock){ok=Examine(lock,fib)&&fib->fib_DirEntryType<0&&(!expected||fib->fib_Size==expected);UnLock(lock);}
    FreeDosObject(DOS_FIB,fib);return ok;
}
static int rom_checksum(const char *name,unsigned profile){
    BPTR f=Open((STRPTR)name,MODE_OLDFILE);UBYTE bytes[1024];ULONG sum=0,crc=0xffffffffu;LONG got;unsigned i,major=0,revision=0,first=1;
    if(!f)return 0;
    while((got=Read(f,bytes,sizeof(bytes)))>0){
        if(got&3){Close(f);return 0;}
        if(first){if(got<16){Close(f);return 0;}major=(bytes[12]<<8)|bytes[13];revision=(bytes[14]<<8)|bytes[15];first=0;}
        for(i=0;i<(unsigned)got;i++)crc=zp_crc_byte(crc,bytes[i]);
        for(i=0;i<(unsigned)got;i+=4){ULONG word=((ULONG)bytes[i]<<24)|((ULONG)bytes[i+1]<<16)|((ULONG)bytes[i+2]<<8)|bytes[i+3];ULONG old=sum;sum+=word;if(sum<old)sum++;}
    }
    Close(f);return got==0 && sum==0xffffffffu && zp_rom_target_ok(crc^0xffffffffu) && zp_rom_matches(profile,major,revision);
}
static int check_rom(unsigned profile,const char *name){
    static const char *versions[]={"1.2","1.3","2.04","2.05"};
    struct Process *process=(struct Process*)FindTask(NULL);
    APTR window=process->pr_WindowPtr;
    const char *result;
    char text[128],label[64];
    /* A missing removable volume must not open an Insert volume requester. */
    process->pr_WindowPtr=(APTR)-1;
    if(!file_size(name,0))result="MISSING";
    else if(!file_size(name,zp_rom_size(profile)) || !rom_checksum(name,profile))result="INVALID";
    else result="OK";
    process->pr_WindowPtr=window;
    snprintf(label,sizeof(label),"%s Kickstart %s",machines[profile],versions[profile]);
    snprintf(text,sizeof(text),"  %-26s .....%s",label,result);
    note(text);
    return !strcmp(result,"MISSING");
}
static void open_scanlines(void){
    char local[ZU_PATH],quoted[ZU_PATH*2+3],cmd[ZU_PATH*2+32];
    const char *tool="SYS:Utilities/ZZScanlines/ZZScanlinesGUI";
    if(!file_size(tool,0))tool="C:ZZScanlinesGUI";
    if(!file_size(tool,0)){
        if(!path(local,"Scanlines/ZZScanlinesGUI") || !file_size(local,0)){
            note("ZZScanlines is missing from the installation.");return;
        }
        tool=local;
    }
    if(!zu_quote(quoted,sizeof(quoted),tool))return;
    snprintf(cmd,sizeof(cmd),"Run >NIL: %s",quoted);
    if(SystemTags(cmd,SYS_Input,0,SYS_Output,0,SYS_Asynch,FALSE,TAG_DONE)<0)
        note("Could not open ZZScanlines.");
    else note("ZZScanlines: firmware controls for low-resolution display modes.");
}
static void check_roms(void){
    unsigned i,missing=0;
    note("");
    note("Kickstart ROMs");
    for(i=0;i<4;i++)missing+=check_rom(i,config.roms[i]);
    if(missing)note("  Missing ROMs: https://retroroms.org");
}
static int check_disk(const char *label,const char *name,int workbench){
    struct Process *process=(struct Process*)FindTask(NULL);
    APTR window=process->pr_WindowPtr;
    const char *result="OK";
    char text[128];
    process->pr_WindowPtr=(APTR)-1;
    if(!file_size(name,0))result="MISSING";
    else if(!file_size(name,901120))result="INVALID";
    else if(workbench){
        unsigned char bytes[1024];BPTR f=Open((STRPTR)name,MODE_OLDFILE);
        LONG size=f?Read(f,bytes,sizeof(bytes)):-1;
        if(f)Close(f);
        if(size!=sizeof(bytes) || !zu_workbench_boot_ok(bytes,sizeof(bytes)))result="INVALID";
    }
    process->pr_WindowPtr=window;
    snprintf(text,sizeof(text),"  %-26s .....%s",label,result);note(text);
    return !strcmp(result,"MISSING");
}
static void check_disks(void){
    static const char *names[]={"Workbench12.adf","Workbench13.adf","Workbench20.adf"};
    static const char *labels[]={"Workbench 1.2","Workbench 1.3","Workbench 2.0"};
    char name[ZU_PATH];unsigned i,missing=0;
    note("");
    note("Workbench disks");
    for(i=0;i<3;i++){
        if(path(name,"Disks") && AddPart(name,(STRPTR)names[i],sizeof(name)))missing+=check_disk(labels[i],name,1);
    }
    check_disk("Selected DF0 (880K ADF)",config.disk,0);
    if(missing)note("  Workbench TOSEC: https://grandis.nu/turran/");
}
static void log_line(const char *line){
    char text[256];unsigned n,elapsed;
    if(!strcmp(line,"STARTUP First frame ready")){loading_end();note("Display ready.");}
    else if(!strncmp(line,"STARTUP ",8))note(line+8);
    else if(!strncmp(line,"OWNED ",6))note("ZZ9000 memory allocated.");
    else if(!strncmp(line,"MAPPING PASS",12))note("Shared-memory mapping verified.");
    else if(!strncmp(line,"ARM ready=",10))note("Cortex-A9 ready.");
    else if(!strncmp(line,"TIMER estimated_hz=",19))note("ARM timer calibrated.");
    else if(sscanf(line,"PROGRESS frames=%u elapsed_us=%u",&n,&elapsed)==2){snprintf(text,sizeof(text),"Running: %u frames displayed.",n);note(text);state(text);}
    else if(sscanf(line,"BOOT elapsed_us=%u rendered_frames=%u",&elapsed,&n)==2){snprintf(text,sizeof(text),"Emulation stopped: %u frames, %u.%02u seconds.",n,elapsed/1000000,(elapsed%1000000)/10000);note(text);}
    else if(!strncmp(line,"MMU_RESTORE phase=3 register_mismatches=00000000",46) && strstr(line,"witness_bad=0"))note("ARM state restored.");
    else if(!strncmp(line,"LAUNCHER exit=",14))note(strstr(line,"exit=0;")?"Session closed; memory released.":"Session ended with an error. See Last-Run.log.");
    else if(strstr(line,"TIMEOUT"))note("Error: the prototype run timed out.");
    else if(!strncmp(line,"FAIL",4)||!strncmp(line,"Missing",7)||!strncmp(line,"ERROR",5)||(strstr(line,"failed")&&!strstr(line,"failed=0"))||strstr(line,"requires")||strstr(line,"instruction bound"))note(line);
}
static void tail_log(void){
    BPTR f=Open((STRPTR)logpath,MODE_OLDFILE);char b[1024];LONG got;unsigned i;
    if(!f)return;
    if(Seek(f,logoffset,OFFSET_BEGINNING)<0){Close(f);return;}
    while((got=Read(f,b,sizeof(b)))>0){
        logoffset+=got;
        for(i=0;i<(unsigned)got;i++){
            if(b[i]=='\n'){partial[partial_size]=0;log_line(partial);partial_size=0;}
            else if(b[i]!='\r' && partial_size+1<sizeof(partial))partial[partial_size++]=b[i];
        }
    }
    Close(f);
}
static void timer_start(void){
    timer->tr_node.io_Command=TR_ADDREQUEST;timer->tr_time.tv_secs=0;timer->tr_time.tv_micro=joy_testing?50000:250000;
    SendIO((struct IORequest*)timer);timer_pending=1;
}
static void timer_stop(void){if(timer_pending){AbortIO((struct IORequest*)timer);WaitIO((struct IORequest*)timer);timer_pending=0;}}
static void stop_player(void){
    struct MsgPort *port;
    if(stop_sent)return;
    Forbid();port=FindPort(stopname);
    if(port){Signal(port->mp_SigTask,SIGBREAKF_CTRL_C);stop_requested=0;stop_sent=1;}
    Permit();
}
static void worker(void){
    job.result=SystemTags(command,SYS_Input,0,SYS_Output,job.log,SYS_Asynch,FALSE,NP_StackSize,131072,TAG_DONE);
    Close(job.log);
    /* No parent code can be unloaded until this return reaches DOS teardown. */
    Forbid();PutMsg(doneport,&job.done);
}
static void launch(void){
    struct DateStamp ds;BPTR f;struct Process *p;char text[96];
    joy_close();timer_stop();
    read_config();
    if(!zu_valid(&config)){note("Error: choose valid Kickstart and disk paths.");state("Check media paths");return;}
    if(FindPort("Sixies.ARM.Debug.Owner")){note("Error: another ZZ9000 ARM application is running.");state("ARM is busy");return;}
    note("Checking Kickstart, DF0 and player...");
    if(!file_size(player,0)){note("Error: ZZUAE-Player is missing from this drawer.");state("Player missing");return;}
    if(!file_size(config.rom,zp_rom_size(config.profile))||!rom_checksum(config.rom,config.profile)){note("Error: matching Kickstart ROM is missing or invalid for this machine.");state("Check Kickstart");return;}
    if(!file_size(config.disk,901120)){note("Error: DF0 needs a raw 880 KiB ADF image.");state("Check DF0 disk");return;}
    DateStamp(&ds);snprintf(session,sizeof(session),"%08lx",(unsigned long)(ds.ds_Days*86400u+ds.ds_Minute*60u+ds.ds_Tick+(++serial)*0x1021u));
    snprintf(stopname,sizeof(stopname),"ZZUAE.Run.%s",session);
    if(!zu_command(command,sizeof(command),player,session,&config)){note("Error: launch command is too long.");return;}
    f=Open((STRPTR)logpath,MODE_NEWFILE);if(!f){note("Error: cannot create Last-Run.log in this drawer.");return;}Close(f);
    memset(&job,0,sizeof(job));job.log=Open((STRPTR)logpath,MODE_READWRITE);
    if(!job.log){note("Error: cannot open the startup log.");return;}
    logoffset=0;partial_size=0;stop_requested=stop_sent=0;
    p=CreateNewProcTags(NP_Entry,(ULONG)worker,NP_Name,(ULONG)"ZZUAE launch worker",NP_StackSize,16384,
        NP_Input,0,NP_Output,0,NP_CloseInput,FALSE,NP_CloseOutput,FALSE,TAG_DONE);
    if(!p){Close(job.log);note("Error: could not start the launch worker.");return;}
    busy=1;controls();state("Starting...");loading_begin();
    snprintf(text,sizeof(text),"Starting %s / PAL, limit %u frames.",machines[config.profile],zu_frames[config.limit]);note(text);timer_start();
}
static void save_settings(void){
    FILE *f;int ok;
    read_config();if(!zu_valid(&config)){note("Error: settings contain an invalid path.");return;}
    f=fopen(cfgpath,"w");if(!f){note("Error: cannot save ZZUAE.cfg.");return;}
    ok=zu_save(f,&config);if(fclose(f))ok=0;
    note(ok?"Settings saved.":"Error writing ZZUAE.cfg.");state(ok?"Settings saved":"Save failed");
}
static int make_icon(const char *name,int drawer){
    struct DiskObject *d;int ok=0;
    IconBase=OpenLibrary("icon.library",39);if(!IconBase)return 20;
    d=GetDiskObject((STRPTR)name);
    if(!d){d=GetDefDiskObject(drawer?WBDRAWER:WBTOOL);if(d){d->do_StackSize=65536;d->do_CurrentX=d->do_CurrentY=NO_ICON_POSITION;ok=PutDiskObject((STRPTR)name,d);}}
    else ok=1;
    if(d)FreeDiskObject(d);CloseLibrary(IconBase);return ok?0:20;
}
int main(int argc,char **argv){
    Object *rombutton,*diskbutton,*joybutton,*scanbutton;ULONG id,signals,open=0;FILE *f;int rc=20,loaded=1;
    if(argc==3&&!strcmp(argv[1],"--make-icon"))return make_icon(argv[2],0);
    if(argc==3&&!strcmp(argv[1],"--make-drawer"))return make_icon(argv[2],1);
    if(!NameFromLock(GetProgramDir(),appdir,sizeof(appdir)))goto done;
    if(!path(player,"ZZUAE-Player")||!path(cfgpath,"ZZUAE.cfg")||!path(logpath,"Last-Run.log"))goto done;
    path(config.roms[0],"ROMs/Kick12.rom");path(config.roms[1],"ROMs/Kick13.rom");
    path(config.roms[2],"ROMs/Kick204.rom");path(config.roms[3],"ROMs/Kick205.rom");
    strcpy(config.rom,config.roms[0]);path(config.disk,"Disks/Workbench12.adf");config.limit=2;config.fps=0;config.ram=1;config.audio=2;config.joystick=1;
    f=fopen(cfgpath,"r");if(f){loaded=zu_load(f,&config);fclose(f);}
    uiport=CreateMsgPort();if(!uiport)goto done;uiport->mp_Node.ln_Name="ZZUAE.Launcher";
    Forbid();if(FindPort(uiport->mp_Node.ln_Name)){Permit();DeleteMsgPort(uiport);uiport=NULL;goto done;}AddPort(uiport);Permit();
    doneport=CreateMsgPort();timerport=CreateMsgPort();if(!doneport||!timerport)goto done;
    timer=(struct timerequest*)CreateIORequest(timerport,sizeof(*timer));if(!timer)goto done;
    if(OpenDevice(TIMERNAME,UNIT_MICROHZ,(struct IORequest*)timer,0))goto done;timer_open=1;
    MUIMasterBase=OpenLibrary("muimaster.library",15);AslBase=OpenLibrary("asl.library",39);
    ExpansionBase=(struct ExpansionBase*)OpenLibrary("expansion.library",0);
    if(!MUIMasterBase||!AslBase||!ExpansionBase){puts("ZZUAE requires MUI and AmigaOS 3.x libraries.");goto done;}
    GfxBase=(struct GfxBase*)OpenLibrary("graphics.library",39);if(!GfxBase)goto done;
    joy_class=MUI_CreateCustomClass(NULL,MUIC_Area,NULL,sizeof(struct joy_data),(APTR)joy_dispatch);if(!joy_class)goto done;
    app=ApplicationObject,MUIA_Application_Title,(ULONG)"ZZUAE",MUIA_Application_Version,(ULONG)ver,
        MUIA_Application_Base,(ULONG)"ZZUAE",MUIA_Application_Description,(ULONG)"Amiga OCS/ECS Emulation on ZZ9000",
        SubWindow,joywin=joy_window(),
        SubWindow,win=WindowObject,MUIA_Window_Title,(ULONG)"ZZUAE Setup " ZU_VERSION,MUIA_Window_ID,0x5a554145,
        MUIA_Window_Width,620,MUIA_Window_Height,430,
        WindowContents,VGroup,MUIA_Group_Spacing,6,
            Child,ListviewObject,MUIA_VertWeight,100,MUIA_Listview_Input,FALSE,
                MUIA_Listview_List,loglist=ListObject,ReadListFrame,MUIA_Font,MUIV_Font_Fixed,
                MUIA_List_ConstructHook,MUIV_List_ConstructHook_String,MUIA_List_DestructHook,MUIV_List_DestructHook_String,End,End,
            Child,settings=VGroup,MUIA_VertWeight,0,
                Child,HGroup,
                    Child,ColGroup(2),Child,label("Machine"),Child,machine=cycle(machines),
                        Child,label("CPU"),Child,readout("68000 compatible"),
                        Child,label("Memory"),Child,ram=cycle(memory_entries(config.profile)),
                        Child,label("Chipset"),Child,chipset=readout(config.profile<2?"OCS / PAL":"ECS / PAL"),
                        Child,label("DF0 writes"),Child,writes=cycle(write_modes),
                        Child,label("Joystick"),Child,joystick=cycle(joy_modes),
                        Child,label("Software"),Child,scanlines=cycle(scan_modes),End,
                    Child,ColGroup(2),Child,label("Output"),Child,output=cycle(outputs),
                        Child,label("Renderer"),Child,renderer=cycle(renderers),
                        Child,label("Frame rate"),Child,fps=cycle(rates),
                        Child,label("Run limit"),Child,limit=cycle(limits),
                        Child,label("Sound"),Child,sound=cycle(sounds),
                        Child,label("Controller"),Child,joybutton=SimpleButton("Joystick test"),
                        Child,label("Firmware"),Child,scanbutton=SimpleButton("ZZScanlines..."),End,End,
                Child,ColGroup(3),Child,label("ROM"),Child,romfield=field(),Child,rombutton=SimpleButton("Browse..."),
                    Child,label("DF0"),Child,diskfield=field(),Child,diskbutton=SimpleButton("Browse..."),End,End,
            Child,HGroup,MUIA_VertWeight,0,Child,label("Status"),Child,status=TextObject,TextFrame,MUIA_Text_Contents,(ULONG)"Ready",End,End,
            Child,HGroup,MUIA_VertWeight,0,Child,save=SimpleButton("Save"),Child,start=SimpleButton("Start"),Child,cancel=SimpleButton("Cancel"),End,
        End,End,End;
    if(!app)goto done;
    set(romfield,MUIA_String_Contents,(ULONG)config.rom);set(diskfield,MUIA_String_Contents,(ULONG)config.disk);
    set(output,MUIA_Cycle_Active,config.output);set(renderer,MUIA_Cycle_Active,config.renderer);
    set(writes,MUIA_Cycle_Active,config.writes);set(limit,MUIA_Cycle_Active,config.limit);set(fps,MUIA_Cycle_Active,config.fps);set(ram,MUIA_Cycle_Active,config.ram);set(machine,MUIA_Cycle_Active,config.profile);set(sound,MUIA_Cycle_Active,config.audio);set(joystick,MUIA_Cycle_Active,config.joystick);set(scanlines,MUIA_Cycle_Active,config.scanlines);
    set(sound,MUIA_ShortHelp,(ULONG)"Paula direct: native stereo output. AHI: configured unit 0. PAL audio timing; 25/30 FPS reduces display work only.");controls();
    notify(win,MUIA_Window_CloseRequest,TRUE,MUIV_Application_ReturnID_Quit);
    notify(cancel,MUIA_Pressed,FALSE,MUIV_Application_ReturnID_Quit);
    notify(scanbutton,MUIA_Pressed,FALSE,ID_SCANLINES);
    set(scanbutton,MUIA_ShortHelp,(ULONG)"Xanxi firmware scanlines. Requires compatible firmware and a low-resolution mode; affects the whole display.");
    notify(joybutton,MUIA_Pressed,FALSE,ID_JOY);notify(joywin,MUIA_Window_CloseRequest,TRUE,ID_JOY_CLOSE);
    notify(start,MUIA_Pressed,FALSE,ID_START);notify(save,MUIA_Pressed,FALSE,ID_SAVE);
    notify(rombutton,MUIA_Pressed,FALSE,ID_ROM);notify(diskbutton,MUIA_Pressed,FALSE,ID_DISK);
    notify(output,MUIA_Cycle_Active,MUIV_EveryTime,ID_OUTPUT);
    notify(sound,MUIA_Cycle_Active,MUIV_EveryTime,ID_OUTPUT);
    notify(machine,MUIA_Cycle_Active,MUIV_EveryTime,ID_MACHINE);
    startup_splash();
    set(win,MUIA_Window_Open,TRUE);get(win,MUIA_Window_Open,&open);if(!open)goto done;
    note("ZZUAE " ZU_VERSION " - Amiga OCS/ECS Emulation on ZZ9000");
    note("UAE/UAE4ARM - Chips-fr and contributors");
    note("XACP / ZZScanlines - Xanxi");
    note("Interface: MUI   Graphics: Picasso96   Audio: AHI");
    note("Development: Codex assisted, Amiga-Bridge MCP");
    note(FindConfigDev(NULL,0x6d6e,4)?"ZZ9000 detected. MUI and file requester ready.":"Error: no ZZ9000 graphics board detected.");
    if(!loaded)note("Error: invalid ZZUAE.cfg; using defaults.");
    check_roms();
    check_disks();
    note("F5 screenshot / F9 scanlines / F10 exit.");
    for(;;){
        if(busy && GetMsg(doneport)){
            timer_stop();tail_log();loading_end();busy=0;controls();
            if(job.result==0){state("Finished");note("Ready for another run.");}
            else {char text[96];snprintf(text,sizeof(text),"Error: player returned %ld. Details are in Last-Run.log.",(long)job.result);note(text);state("Run failed");}
            if(closing)break;
        }
        if(timer_pending && CheckIO((struct IORequest*)timer)){
            WaitIO((struct IORequest*)timer);timer_pending=0;if(busy)tail_log();if(joy_testing)joy_sample();
            if(stop_requested)stop_player();
            if(busy||joy_testing)timer_start();
        }
        id=DoMethod(app,MUIM_Application_NewInput,(ULONG)&signals);
        if(id==(ULONG)MUIV_Application_ReturnID_Quit){
            if(!busy)break;
            if(val(win,MUIA_Window_CloseRequest))closing=1;
            stop_requested=1;stop_player();state("Stopping...");
        }else if(!busy){
            if(id==ID_START)launch();else if(id==ID_SAVE)save_settings();
            else if(id==ID_ROM){browse(romfield,"Select the matching Kickstart ROM");read_config();check_rom(config.profile,config.rom);}
            else if(id==ID_DISK){browse(diskfield,"Select an 880 KiB ADF disk");read_config();check_disk("Selected DF0 (880K ADF)",config.disk,0);}
            else if(id==ID_OUTPUT)controls();
            else if(id==ID_SCANLINES)open_scanlines();
            else if(id==ID_MACHINE)select_machine();
            else if(id==ID_JOY){
                if(!LowLevelBase)LowLevelBase=OpenLibrary("lowlevel.library",40);
                set(joywin,MUIA_Window_Open,TRUE);joy_testing=1;joy_last=~0ul;joy_sample();
                if(!timer_pending)timer_start();
            }else if(id==ID_JOY_CLOSE){joy_close();timer_stop();}
        }
        if(!id && signals){
            ULONG got=Wait(signals|(1ul<<doneport->mp_SigBit)|(1ul<<timerport->mp_SigBit)|SIGBREAKF_CTRL_C);
            if(got&SIGBREAKF_CTRL_C){if(!busy)break;closing=stop_requested=1;stop_player();}
        }
    }
    rc=0;
done:
    timer_stop();if(loading_window)loading_end();if(app)MUI_DisposeObject(app);
    if(joy_class)MUI_DeleteCustomClass(joy_class);
    if(GfxBase)CloseLibrary((struct Library*)GfxBase);
    if(LowLevelBase)CloseLibrary(LowLevelBase);
    if(ExpansionBase)CloseLibrary((struct Library*)ExpansionBase);
    if(AslBase)CloseLibrary(AslBase);if(MUIMasterBase)CloseLibrary(MUIMasterBase);
    if(timer_open)CloseDevice((struct IORequest*)timer);if(timer)DeleteIORequest((struct IORequest*)timer);
    if(timerport)DeleteMsgPort(timerport);if(doneport)DeleteMsgPort(doneport);
    if(uiport){RemPort(uiport);DeleteMsgPort(uiport);}return rc;
}
