/* Disposable-disk test; never run against personal disks. DF1 starts with A,
 * then swaps to B and back to A. All files close before waiting for a change.
 * No C runtime: its utility.library dependency would exclude Kickstart 1.3. */
#include <exec/execbase.h>
#include <proto/exec.h>
#include <proto/dos.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
static unsigned length(const char *s){unsigned n=0;while(s[n])n++;return n;}
static int same(const char *a,const char *b){while(*a && *a==*b){a++;b++;}return *a==*b;}
static int read_text(const char *path,char *text,unsigned size){
 BPTR f=Open((STRPTR)path,MODE_OLDFILE);if(!f)return 0;
 LONG n=Read(f,text,size-1);Close(f);
 if(n<0)return 0;
 text[n]=0;return 1;
}
static int write_text(const char *path,const char *text){
 BPTR f=Open((STRPTR)path,MODE_NEWFILE);if(!f)return 0;
 LONG n=length(text);int ok=Write(f,(APTR)text,n)==n;
 if(!Close(f))ok=0;
 return ok;
}
static void say(const char *text){Write(Output(),(APTR)text,length(text));}
static int wait_disk(char name){
 char text[64];
 for(unsigned i=0;i<480;i++){
  if(read_text("DF1:Marker",text,sizeof text)&&text[0]==name){Delay(250);return 1;}
  Delay(25);
 }
 return 0;
}
LONG start(void){
 SysBase=*(struct ExecBase**)4;
 DOSBase=(struct DosLibrary*)OpenLibrary("dos.library",0);if(!DOSBase)return 20;
 char text[64];int ok=0;
 say("ZZUAE disposable disk test: waiting for A\n");
 if(!wait_disk('A')||!write_text("DF1:Saved.txt","A-first\n"))goto done;
 Delay(500);say("Swap DF1 to B\n");
 if(!wait_disk('B')||!write_text("DF1:Saved.txt","B-first\n"))goto done;
 Delay(500);say("Reinsert A in DF1\n");
 if(!wait_disk('A')||!read_text("DF1:Saved.txt",text,sizeof text)||!same(text,"A-first\n"))goto done;
 if(!write_text("DF1:Saved.txt","A-final\n"))goto done;
 Delay(500);ok=1;
 done:
 write_text("DF0:SwapResult.txt",ok?"PASS guest write, swap, reinsert, readback\n":"FAIL guest disk swap\n");
 say(ok?"PASS guest disk swap\n":"FAIL guest disk swap\n");Delay(500);
 CloseLibrary((struct Library*)DOSBase);return ok?0:20;
}
