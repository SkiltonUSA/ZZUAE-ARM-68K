/* GPL-3.0-or-later. Install missing Xanxi tools; never replace existing tools. */
#include <exec/types.h>
#include <dos/dos.h>
#include <dos/dosextens.h>
#include <intuition/intuition.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/intuition.h>
#include <stdio.h>
#include <string.h>
struct IntuitionBase *IntuitionBase;
/* 0 absent, 1 regular file, -1 directory/error. */
static int file_status(const char *path){
 BPTR lock=Lock((STRPTR)path,ACCESS_READ);struct FileInfoBlock fib;int ok;
 if(!lock)return IoErr()==ERROR_OBJECT_NOT_FOUND?0:-1;
 ok=Examine(lock,&fib)&&fib.fib_DirEntryType<0;UnLock(lock);return ok?1:-1;
}
static int directory(const char *path){
 BPTR lock=Lock((STRPTR)path,ACCESS_READ);struct FileInfoBlock fib;int ok;
 if(lock){ok=Examine(lock,&fib)&&fib.fib_DirEntryType>0;UnLock(lock);return ok;}
 lock=CreateDir((STRPTR)path);if(!lock)return 0;UnLock(lock);return 1;
}
static int install_one(const char *name,const char *dest,int alternate){
 char src[256],target[256],command[80];BPTR in=0,out=0;char buf[4096];LONG n;int ok=0,status;
 if(snprintf(src,sizeof(src),"PROGDIR:Scanlines/%s",name)>=(int)sizeof(src)||snprintf(target,sizeof(target),"%s/%s",dest,name)>=(int)sizeof(target))return -1;
 status=file_status(target);if(status==1){printf("Kept existing %s\n",target);return 0;}if(status<0)return -1;
 if(alternate){snprintf(command,sizeof(command),"C:%s",name);status=file_status(command);if(status==1){printf("Kept existing %s\n",command);return 0;}if(status<0)return -1;}
 in=Open((STRPTR)src,MODE_OLDFILE);if(!in)return -1;
 out=Open((STRPTR)target,MODE_NEWFILE);if(!out){Close(in);return -1;}
 while((n=Read(in,buf,sizeof(buf)))>0){if(Write(out,buf,n)!=n)break;}
 ok=n==0;if(!Close(out))ok=0;Close(in);
 if(ok)ok=SetProtection((STRPTR)target,0);
 if(!ok){DeleteFile((STRPTR)target);return -1;}
 printf("Installed %s\n",target);return 1;
}
int main(int argc,char **argv){
 const char *dest=argc>1?argv[1]:"SYS:Utilities/ZZScanlines";
 int rc=20,cli=-1,gui=-1;char text[256];
 if(argc>2){puts("Usage: Install-Scanlines [destination drawer]");return 20;}
 if(argc>1||directory("SYS:Utilities")){
  if(directory(dest)){
   cli=install_one("ZZScanlines",dest,argc<=1);
   gui=install_one("ZZScanlinesGUI",dest,argc<=1);
   if(cli>=0&&gui>=0)rc=0;
  }
 }
 snprintf(text,sizeof(text),rc?"Scanline tools could not be installed.\nCheck the package files and destination.":"Xanxi scanline tools ready.\n%d added; existing tools preserved.\nCompatible FPGA firmware is required.\nFirmware and startup files were not changed.",(cli>0)+(gui>0));
 puts(text);
 if(argc==0){
  IntuitionBase=(struct IntuitionBase *)OpenLibrary("intuition.library",37);
  if(IntuitionBase){struct EasyStruct e={sizeof(e),0,(UBYTE *)"Xanxi Scanlines",(UBYTE *)text,(UBYTE *)"OK"};EasyRequestArgs(NULL,&e,NULL,NULL);CloseLibrary((struct Library *)IntuitionBase);}
 }
 return rc;
}
