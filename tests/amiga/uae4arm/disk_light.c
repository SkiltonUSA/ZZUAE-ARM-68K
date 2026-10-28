#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "disk_light.h"
int main(void){
 struct zu_disk_light s={0};
 assert(!zu_disk_light_update(&s,0,1000000,1));
 assert(zu_disk_light_update(&s,1,1000001,1));
 assert(zu_disk_light_update(&s,2,1040000,1));
 assert(!zu_disk_light_update(&s,3,1060001,1));
 assert(!zu_disk_light_update(&s,4,1090000,1));
 assert(zu_disk_light_update(&s,4,1100001,1));
 assert(!zu_disk_light_update(&s,4,1160001,1));
 assert(!zu_disk_light_update(&s,4,1200001,1));
 assert(zu_disk_light_update(&s,5,1300000,1));
 assert(!zu_disk_light_update(&s,5,1300001,0));
 assert(!zu_disk_light_update(&s,5,1500000,1));
 s=(struct zu_disk_light){.seen=UINT32_MAX,.changed=UINT32_MAX-100000};
 assert(zu_disk_light_update(&s,0,UINT32_MAX-1000,1));
 assert(!zu_disk_light_update(&s,0,60000,1));
 assert(!zu_disk_light_update(&s,0,1000000,1));
 struct zu_disk_light drives[2]={{0},{0}};
 assert(zu_disk_light_update(&drives[0],1,1000000,1));
 assert(!zu_disk_light_update(&drives[1],0,1000000,1));
 assert(!zu_disk_light_update(&drives[0],1,1060000,1));
 assert(zu_disk_light_update(&drives[1],1,1060000,1));
 assert(!zu_disk_light_update(&drives[0],1,1100000,1));
 assert(zu_disk_light_update(&drives[1],1,1100000,1));
 puts("PASS disk read pulses: idle, coalescing, off gap, stop and counter/timer wrap");
}
