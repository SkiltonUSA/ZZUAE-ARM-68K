#include "launcher_config.h"
#include <assert.h>
int main(void){
 struct zu_config c={.rom="ROMs/Kick31-A1200.rom",.disk="Disks/AGA.adf",.profile=4,.engine=2};
 char cmd[4096];struct zu_config d=c;
 assert(zp_chip(4,0)==0x200000 && zp_chip(4,1)==0x200000);
 assert(zp_rom_size(4)==0x80000);
 assert(zp_rom_matches(4,39,106)&&zp_rom_matches(4,40,68));
 assert(zp_rom_matches(4,46,143));
 assert(!zp_rom_matches(4,46,142));
 assert(!zp_rom_matches(4,37,350));
 assert(zu_valid(&c));assert(zu_command(cmd,sizeof cmd,zu_player(&c),"12345678",&c));
 assert(strstr(cmd,"MODEL A1200") && strstr(cmd,"ENGINE INTERPRETER020"));
 FILE*f=tmpfile();assert(f&&zu_save(f,&c));rewind(f);assert(zu_load(f,&d));fclose(f);assert(d.profile==4);
 c.engine=0;assert(!zu_valid(&c));c.engine=3;assert(!zu_valid(&c));
 puts("PASS A1200 CPU, RAM, ROM selection and persistence");
}
