#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "filesys.h"
#include "machine.h"
#include "storage_wire.h"
#include "protocol.h"
extern uint64_t zzuae_clock_us(void);
static unsigned sequence;
extern "C" int zu_storage_io(unsigned unit,unsigned op,uint64_t offset,void *buffer,unsigned bytes){
 uint64_t total=unit<2?UAE_DISK_SIZE:ad_get(uae_shared,US_HDF_SIZE);unsigned done=0;
 if(unit==2)total|=(uint64_t)ad_get(uae_shared,US_HDF_HIGH)<<32;
 if(unit>2 || !bytes || (bytes&511) || offset>total || bytes>total-offset)return 0;
 if(op==US_WRITE && unit==2 && ad_get(uae_shared,US_USB_DISK))return 0;
 if(op==US_WRITE && !ad_get(uae_shared,US_WRITABLE))return 0;
 while(done<bytes){
  unsigned n=bytes-done;if(n>US_CAPACITY)n=US_CAPACITY;
  if(uae_stop && uae_stop())return 0;
  if(op==US_WRITE)memcpy((void*)(uae_shared+US_DATA),(uint8_t*)buffer+done,n);
  ad_put(uae_shared,US_OPERATION,op);ad_put(uae_shared,US_UNIT,unit);
  ad_put(uae_shared,US_OFFSET,(uint32_t)(offset+done));ad_put(uae_shared,US_OFFSET_HIGH,(uint32_t)((offset+done)>>32));ad_put(uae_shared,US_LENGTH,n);
  __asm__ volatile("dsb sy":::"memory");ad_put(uae_shared,US_REQUEST,++sequence);
  __asm__ volatile("dsb sy":::"memory");
  uint64_t start=zzuae_clock_us();
  while(ad_get(uae_shared,US_REPLY)!=sequence){
   if((uae_stop && uae_stop()) || zzuae_clock_us()-start>10000000u)return 0;
  }
  __asm__ volatile("dsb sy":::"memory");
  if(ad_get(uae_shared,US_RESULT)!=n)return 0;
  if(op==US_READ)memcpy((uint8_t*)buffer+done,(const void*)(uae_shared+US_DATA),n);
  done+=n;
 }
 return bytes;
}
int hdf_read(hardfiledata*,void*p,uae_u64 offset,int bytes){
 return bytes<0?0:zu_storage_io(2,US_READ,offset,p,bytes);
}
int hdf_write(hardfiledata*,void*p,uae_u64 offset,int bytes){
 return bytes<0?0:zu_storage_io(2,US_WRITE,offset,p,bytes);
}
