#include "launcher_config.h"
#include <assert.h>
int main(void){
    struct zu_config c={0},d={0};FILE *f;char cmd[4096];unsigned p;
    uint32_t crc=0xffffffff;const char *test="123456789";
    while(*test)crc=zp_crc_byte(crc,*test++);assert((crc^0xffffffff)==0xcbf43926);
    assert(!zp_rom_target_ok(0x234a7233)&&!zp_rom_target_ok(0xe0f37258));assert(zp_rom_target_ok(0xc3bdb240));
    const unsigned chip[4][2]={{0x40000,0x80000},{0x80000,0x80000},{0x100000,0x200000},{0x100000,0x200000}};
    for(p=0;p<4;p++){
        assert(zp_chip(p,0)==chip[p][0] && zp_chip(p,1)==chip[p][1]);
        assert(zp_slow(p,0)==0 && zp_slow(p,1)==(p==1?0x80000u:0));
        snprintf(c.roms[p],ZU_PATH,"DH0:ROMs/machine%u.rom",p);
    }
    assert(zp_rom_matches(0,33,166));assert(!zp_rom_matches(0,34,5));
    assert(zp_rom_matches(1,34,5));assert(!zp_rom_matches(1,37,175));
    assert(zp_rom_matches(2,37,175));assert(!zp_rom_matches(2,37,350));
    assert(zp_rom_matches(3,37,299)&&zp_rom_matches(3,37,300)&&zp_rom_matches(3,37,350));
    assert(!zp_rom_matches(3,37,175));assert(!zp_rom_matches(4,40,68));
    strcpy(c.disk,"DH0:Workbench.adf");c.fps=2;c.ram=1;c.profile=3;strcpy(c.rom,c.roms[3]);
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d));fclose(f);
    assert(d.profile==3&&d.ram==1);
    for(p=0;p<4;p++)assert(!strcmp(c.roms[p],d.roms[p]));
    assert(zu_command(cmd,sizeof(cmd),"player","10260001",&c));assert(strstr(cmd,"MODEL A600"));
    c.profile=4;assert(!zu_valid(&c));
    puts("PASS: machine RAM/chipset selection contract, ROM-family rejection, per-machine ROM persistence");
}
