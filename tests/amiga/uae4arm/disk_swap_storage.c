/* Transaction ordering and failure tests for the actual host swap routine. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <stdint.h>
#include <unistd.h>
#include "disk_swap.h"
#define UAE_DISK_SIZE 901120u
#define UAE_DISK 0u
#define UAE_DISK1_OFFSET UAE_DISK_SIZE
#define MEMF_PUBLIC 0
#define APTR void *
#define AllocVec(n,f) malloc(n)
#define FreeVec(p) free(p)
#define CopyMem(a,b,n) memcpy(b,a,n)
struct us_host_file {char path[512];unsigned size;int lock;char lockpath[1024];};
static struct us_host_file us_files[3];
static unsigned char shared[UAE_DISK_SIZE*2];
static int persistent_mode,live_quit,reply=UM_OK,commands,closed,prepared,writes_seen,insert_failure;
static char old_path[512];
static void push(void *p,unsigned n,void *x){(void)x;assert(n==UAE_DISK_SIZE);assert(p==shared||p==shared+UAE_DISK_SIZE);}
static void barrier(void*x){(void)x;}
static struct {void(*push)(void*,unsigned,void*);void(*barrier)(void*);} ops={push,barrier},*syncio=&ops;
static void live_abort(void){live_quit=1;}
static void us_close_file(struct us_host_file*f){if(f->lock)closed++;memset(f,0,sizeof *f);}
static int us_prepare_file(struct us_host_file*f,unsigned unit,const char*p,int writable){
 assert(unit<2);prepared++;writes_seen=writable;strcpy(f->path,p);f->lock=1;
 FILE *in=fopen(p,"rb");if(!in)return 0;fseek(in,0,SEEK_END);long n=ftell(in);fclose(in);return n==UAE_DISK_SIZE;
}
static unsigned live_media_request(unsigned op,unsigned unit){
 assert(unit<2);commands++;
 if(op==UM_EJECT)assert(!strcmp(us_files[unit].path,old_path));
 else {assert(op==UM_INSERT);assert(us_files[unit].lock);assert(shared[unit*UAE_DISK_SIZE]==0xa5);}
 return op==UM_INSERT&&insert_failure?UM_INVALID:reply;
}
#include "disk_swap_storage.inc"
static void setup(const char *path){memset(us_files,0,sizeof us_files);strcpy(old_path,path);strcpy(us_files[0].path,path);us_files[0].lock=1;commands=closed=prepared=live_quit=insert_failure=0;reply=UM_OK;}
int main(void){
 char tmp[]="/tmp/zzuae-swap-XXXXXX";char *d=mkdtemp(tmp);assert(d);
 char valid[512],shortfile[512],missing[512];snprintf(valid,sizeof valid,"%s/valid.adf",d);snprintf(shortfile,sizeof shortfile,"%s/short.adf",d);snprintf(missing,sizeof missing,"%s/missing.adf",d);
 FILE*f=fopen(valid,"wb");assert(f);for(unsigned i=0;i<UAE_DISK_SIZE;i++)fputc(0xa5,f);assert(!fclose(f));
 f=fopen(shortfile,"wb");assert(f);fputc(0,f);fclose(f);
 for(unsigned i=0;i<2;i++){setup("old.adf");assert(!us_swap_disk(0,i?shortfile:missing));assert(!commands&&!strcmp(us_files[0].path,"old.adf")&&us_files[0].lock);}
 setup("old.adf");reply=UM_BUSY;assert(!us_swap_disk(0,valid));assert(commands==1&&!strcmp(us_files[0].path,"old.adf")&&closed==1);
 setup("old.adf");persistent_mode=1;assert(us_swap_disk(0,valid));assert(commands==2&&closed==1&&writes_seen&&us_files[0].lock&&!strcmp(us_disk_name(0),valid));
 setup(valid);assert(us_swap_disk(0,valid));assert(commands==2&&!closed&&!prepared&&us_files[0].lock);
 setup("old.adf");insert_failure=1;assert(!us_swap_disk(0,valid));assert(commands==2&&live_quit&&us_files[0].lock&&!strcmp(us_disk_name(0),valid));
 setup(valid);assert(us_swap_disk(0,""));assert(commands==1&&closed==1&&!us_files[0].path[0]&&!us_files[0].lock);
 setup(valid);assert(!us_swap_disk(2,valid));assert(!commands);
 unlink(valid);unlink(shortfile);rmdir(d);
 puts("PASS disk swap transaction: failed preparation/busy keep old disk; same-image reinsertion; commit and eject; insertion failure stops; persistent mode retained");
}
