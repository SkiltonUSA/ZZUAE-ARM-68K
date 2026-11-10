#include <assert.h>
#include <stdio.h>
#include "../../../amiga/uae4arm/usb_rdb.h"

struct disk {unsigned char sectors[17][512];unsigned reads,limit;int fail;};
static void word(unsigned char*p,uint32_t v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static int read_sector(void *ctx,uint64_t offset,void *data,unsigned bytes){
 struct disk*d=ctx;unsigned sector=offset/512;
 assert(bytes==512 && offset%512==0 && sector<d->limit);
 d->reads++;if((int)sector==d->fail)return 0;
 memcpy(data,d->sectors[sector],512);return 1;
}
static void header(struct disk*d,unsigned sector){
 unsigned char*p=d->sectors[sector];memcpy(p,"RDSK",4);
 word(p+4,64);word(p+16,512);word(p+8,0u-0x5244534bu-64u-512u);
}
static int check(struct disk*d){d->reads=0;return zu_usb_find_rdb(d,(uint64_t)d->limit*512,read_sector);}
int main(void){
 struct disk d={.limit=17,.fail=-1};
 header(&d,0);assert(check(&d)&&d.reads==1);
 memset(d.sectors,0,sizeof d.sectors);header(&d,2);assert(check(&d)&&d.reads==3);
 d.sectors[2][20]^=1;assert(!check(&d));d.sectors[2][20]^=1;
 word(d.sectors[2]+16,1024);assert(!check(&d));word(d.sectors[2]+16,512);
 d.fail=1;assert(!check(&d)&&d.reads==2);d.fail=-1;
 memset(d.sectors,0,sizeof d.sectors);header(&d,15);assert(check(&d)&&d.reads==16);
 memset(d.sectors,0,sizeof d.sectors);header(&d,16);assert(!check(&d)&&d.reads==16);
 d.limit=1;assert(!check(&d)&&d.reads==1);
 puts("USB RDB search: offset headers, bounds, checksum and I/O failures PASS");
}
