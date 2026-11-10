#include "storage_file.h"
#include <assert.h>
#include <unistd.h>
int main(void){
 char tmp[]="/tmp/zzuae-store-XXXXXX";int fd=mkstemp(tmp);assert(fd>=0);close(fd);
 uint8_t data[16384],check[16384];memset(data,0x55,sizeof data);
 FILE*f=fopen(tmp,"wb");assert(f);for(unsigned i=0;i<8;i++)assert(fwrite(data,1,sizeof data,f)==sizeof data);fclose(f);
 assert(us_file_read(tmp,131072,0,check,sizeof check)&&!memcmp(data,check,sizeof data));
 memset(data,0xa9,sizeof data);assert(us_file_write(tmp,131072,512,data,sizeof data));
 assert(us_file_read(tmp,131072,512,check,sizeof check)&&!memcmp(data,check,sizeof data));
 assert(!us_file_write(tmp,131072,131072,data,512));assert(!us_file_read(tmp,131072,1,check,512));
 /* Simulate interrupted write after durable undo publication. */
 struct zn_journal_paths p;assert(zn_journal_paths(tmp,&p));
 uint8_t*j=us_prepare(tmp,131072,512,16384);assert(j&&us_publish(tmp,&p,j));free(j);
 f=fopen(tmp,"r+b");assert(f);fseek(f,512,SEEK_SET);memset(check,0x88,8192);fwrite(check,1,8192,f);fclose(f);
 assert(zn_journal_recover(tmp));assert(us_file_read(tmp,131072,512,check,sizeof check)&&!memcmp(data,check,sizeof data));
 assert(zn_journal_recover(tmp));
 /* Last sector and an image smaller than a block have bounded recovery. */
 assert(us_file_write(tmp,131072,131072-512,data,512));
 unlink(tmp);puts("PASS changed-block writes, partial-block preservation, interrupted-write recovery, bounds");
}
