#ifndef ZZUAE_DISK_CHECK_H
#define ZZUAE_DISK_CHECK_H
#include <stdint.h>
#include <stddef.h>
/* Standard bootable Workbench ADF. Custom game boot blocks are not subject
 * to the DOS signature requirement. This is not a filesystem/version audit. */
static int zu_workbench_boot_ok(const unsigned char *bytes,size_t size){
    uint32_t sum=0;
    size_t i;
    if(size!=1024 || bytes[0]!='D' || bytes[1]!='O' || bytes[2]!='S')return 0;
    for(i=0;i<size;i+=4){
        uint32_t word=((uint32_t)bytes[i]<<24)|((uint32_t)bytes[i+1]<<16)|
            ((uint32_t)bytes[i+2]<<8)|bytes[i+3];
        uint32_t old=sum;
        sum+=word;if(sum<old)sum++;
    }
    return sum==0xffffffffu;
}
#endif
