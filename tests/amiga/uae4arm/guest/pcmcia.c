/* Run only with a disposable CF image filled with 0x55. Writes sector 3.
 * Start from entry.s with -nostdlib; ROM/library calls need no C runtime. */
#include <exec/execbase.h>
#include <exec/io.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
static unsigned length(const char*s){unsigned n=0;while(s[n])n++;return n;}
static void say(const char*s){Write(Output(),(APTR)s,length(s));}
LONG start(void){
    SysBase=*(struct ExecBase**)4;
    DOSBase=(struct DosLibrary*)OpenLibrary("dos.library",0);if(!DOSBase)return 20;
    const char *result="FAIL create IO request\n";
    struct MsgPort *port=CreateMsgPort();
    struct IOStdReq *io=port?(struct IOStdReq*)CreateIORequest(port,sizeof(*io)):0;
    int opened=0,ok=0;unsigned char data[512];
    say("ZZUAE disposable PCMCIA test\n");
    if(!io)goto done;
    result="FAIL open compactflash.device\n";
    if(OpenDevice("compactflash.device",0,(struct IORequest*)io,0))goto done;
    opened=1;Delay(250);result="FAIL initial CF read\n";
    for(unsigned retry=0;retry<20;retry++){
        io->io_Command=CMD_READ;io->io_Data=data;io->io_Length=512;io->io_Offset=1536;
        if(!DoIO((struct IORequest*)io)&&io->io_Actual==512){ok=1;break;}
        Delay(50);
    }
    if(!ok)goto done;
    ok=0;result="FAIL unexpected CF contents; not writing\n";
    for(unsigned i=0;i<512;i++)if(data[i]!=0x55)goto done;
    for(unsigned i=0;i<512;i++)data[i]=(unsigned char)(i*13+9);
    io->io_Command=CMD_WRITE;io->io_Length=512;io->io_Offset=1536;
    result="FAIL CF write\n";
    if(DoIO((struct IORequest*)io)||io->io_Actual!=512)goto done;
    for(unsigned i=0;i<512;i++)data[i]=0;
    io->io_Command=CMD_READ;io->io_Length=512;io->io_Offset=1536;
    result="FAIL CF readback\n";
    if(DoIO((struct IORequest*)io)||io->io_Actual!=512)goto done;
    for(unsigned i=0;i<512;i++)if(data[i]!=(unsigned char)(i*13+9))goto done;
    result="PASS guest compactflash.device read/write/readback\n";ok=1;
done:
    if(opened)CloseDevice((struct IORequest*)io);
    if(io)DeleteIORequest((struct IORequest*)io);
    if(port)DeleteMsgPort(port);
    BPTR file=Open("DF0:CFResult.txt",MODE_NEWFILE);
    if(file){Write(file,(APTR)result,length(result));Close(file);}
    say(result);Delay(500);CloseLibrary((struct Library*)DOSBase);return ok?0:20;
}
