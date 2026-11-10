#include "fast_memory.h"
#include "launcher_config.h"
#include <assert.h>
static unsigned decode(unsigned size,unsigned reg){unsigned hi=zu_fast_config_byte(size,reg),lo=zu_fast_config_byte(size,reg+2);if(reg!=0 && reg!=0x40){hi=~hi;lo=~lo;}return (hi&0xf0)|((lo>>4)&15);}
int main(void){struct zu_config c={0},d={0};char cmd[4096];strcpy(c.rom,"Kick205.rom");c.profile=ZP_A600;
 for(unsigned i=1;i<=3;i++){
  unsigned size=zu_fast_size(i);assert(size==(0x100000u<<i));assert(decode(size,0)==zu_fast_type(size));assert(decode(size,4)==81);assert(decode(size,0x10)==7);assert(decode(size,0x14)==0xdb);
  c.ram=i+1;assert(zu_valid(&c));assert(zu_command(cmd,sizeof cmd,"player","12345678",&c));assert(strstr(cmd,i==1?"RAM FAST2":i==2?"RAM FAST4":"RAM FAST8"));
  FILE*f=tmpfile();assert(f&&zu_save(f,&c));rewind(f);assert(zu_load(f,&d));assert(d.ram==c.ram);fclose(f);
 }
 assert(zu_fast_size(0)==0&&zu_fast_size(4)==0);c.engine=2;assert(zu_valid(&c));assert(!strcmp(zu_player(&c),"ZZUAE-JIT"));c.engine=1;assert(!zu_valid(&c));c.engine=0;c.profile=ZP_A500;assert(!zu_valid(&c));puts("PASS A600 Fast RAM autoconfig descriptors, commands, settings and model limits");return 0;}
