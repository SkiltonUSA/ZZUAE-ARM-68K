/* Guest filesystem test on a disposable, mounted CF0: FAT volume. */
#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
static unsigned length(const char*s){unsigned n=0;while(s[n])n++;return n;}
static int read_matches(const char*path,const char*expected){
    unsigned char data[80];BPTR f=Open((STRPTR)path,MODE_OLDFILE);if(!f)return 0;
    LONG n=Read(f,data,sizeof data);Close(f);unsigned size=length(expected);
    if(n!=(LONG)size)return 0;
    for(unsigned i=0;i<size;i++)if(data[i]!=(unsigned char)expected[i])return 0;
    return 1;
}
static int write_text(const char*path,const char*text){
    BPTR f=Open((STRPTR)path,MODE_NEWFILE);if(!f)return 0;
    unsigned n=length(text);int ok=Write(f,(APTR)text,n)==(LONG)n;
    if(!Close(f))ok=0;
    return ok;
}
LONG start(void){
    SysBase=*(struct ExecBase**)4;
    DOSBase=(struct DosLibrary*)OpenLibrary("dos.library",0);if(!DOSBase)return 20;
    const char*result="FAIL read FAT marker\n";int ok=0;
    Delay(250);
    if(!read_matches("CF0:Marker.txt","ZZUAE FAT transfer test\n"))goto done;
    result="FAIL write FAT file\n";
    if(!write_text("CF0:Saved.txt","Saved by guest AmigaOS through PCMCIA\n"))goto done;
    result="FAIL read FAT file\n";
    if(!read_matches("CF0:Saved.txt","Saved by guest AmigaOS through PCMCIA\n"))goto done;
    result="PASS guest FAT file read/write/readback\n";ok=1;
done:
    write_text("DF0:FATResult.txt",result);Write(Output(),(APTR)result,length(result));
    Delay(500);CloseLibrary((struct Library*)DOSBase);return ok?0:20;
}
