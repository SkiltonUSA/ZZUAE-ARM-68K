#include "disk_check.h"
#include <assert.h>
#include <stdio.h>
int main(void){
    unsigned char block[1024]={ 'D','O','S',0,0xbb,0xb0,0xac,0xff };
    assert(zu_workbench_boot_ok(block,sizeof(block)));
    assert(!zu_workbench_boot_ok(block,512));
    block[100]=1;assert(!zu_workbench_boot_ok(block,sizeof(block)));block[100]=0;
    block[0]='X';assert(!zu_workbench_boot_ok(block,sizeof(block)));
    puts("PASS: Workbench boot signature, checksum and truncated block rejection");
    return 0;
}
