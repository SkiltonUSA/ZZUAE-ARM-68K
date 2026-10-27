#include "launcher_config.h"
#include <assert.h>
int main(void){
    struct zu_config c={"DH0:ROMs/Kick12.rom","DH0:Games/Some *$`\" disk.adf",0,0,1,2,2,0,1,0,1,0,{{0}},0,0,0,1},d=c;
    char cmd[4096],small[8];FILE *f;
    assert(c.fps==2);
    assert(zu_command(cmd,sizeof(cmd),"SD032G:Emulator/ZZUAE/ZZUAE-Player","1234abcd",&c));
    assert(strstr(cmd," 1800 LIVE WRITE ROM "));
    assert(strstr(cmd," FPS MAX"));
    c.fps=0;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," FPS 25"));
    c.fps=1;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," FPS 30"));
    assert(strstr(cmd,"Some ***$*`*\" disk.adf"));
    assert(!zu_command(small,sizeof(small),"player","1234abcd",&c));
    assert(!zu_command(cmd,sizeof(cmd),"player","1234;run",&c));
    c.output=1;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));
    assert(!strstr(cmd," LIVE")&&!strstr(cmd," COPY"));
    c.output=0;c.renderer=1;c.writes=0;c.ram=1;
    assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," COPY ROM "));assert(strstr(cmd," RAM EXPANDED MODEL A500"));
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d));fclose(f);
    assert(!strcmp(c.rom,d.rom)&&!strcmp(c.disk,d.disk)&&c.renderer==d.renderer&&d.writes==0&&d.fps==1&&d.ram==1);
    f=tmpfile();assert(f);fputs("disk=changed\nlimit=999\n",f);rewind(f);
    assert(!zu_load(f,&d));fclose(f);assert(!strcmp(c.disk,d.disk));
    c.audio=1;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," AUDIO PAULA")&&strstr(cmd," FPS 30"));
    c.audio=2;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," AUDIO AHI"));
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d)&&d.audio==2);fclose(f);
    c.output=1;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," AUDIO OFF"));
    c.scanlines=3;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));
    assert(strstr(cmd," SCANLINES 3"));
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d)&&d.scanlines==3&&d.scanstyle==2);fclose(f);
    c.scanstyle=2;c.scanlines=0;
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d)&&d.scanlines==0&&d.scanstyle==2);fclose(f);
    d.scanlines=d.scanstyle+1;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&d));assert(strstr(cmd," SCANLINES 3"));
    f=tmpfile();assert(f);fputs("scanlines=2\n",f);rewind(f);assert(zu_load(f,&d)&&d.scanlines==3&&d.scanstyle==2);fclose(f);
    f=tmpfile();assert(f);fputs("scanstyle=3\n",f);rewind(f);assert(!zu_load(f,&d));fclose(f);
    for(unsigned old=0;old<4;old++){
        static const unsigned mapped[]={0,2,3,1};
        f=tmpfile();assert(f);fprintf(f,"scanlines=%u\nscanstyle=2\n",old);rewind(f);
        assert(zu_load(f,&d));fclose(f);assert(d.scanlines==mapped[old]);
        assert(d.scanstyle==(old?mapped[old]-1:0));
        f=tmpfile();assert(f);assert(zu_save(f,&d));rewind(f);
        struct zu_config again=d;assert(zu_load(f,&again));fclose(f);
        assert(again.scanlines==d.scanlines && again.scanstyle==d.scanstyle);
    }
    c.scanlines=4;assert(!zu_valid(&c));c.scanlines=0;
    c.engine=1;
    assert(zu_command(cmd,sizeof(cmd),"ZZUAE-JIT","1234abcd",&c));
    assert(strstr(cmd," ENGINE JIT"));
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d)&&d.engine==1);fclose(f);
    c.engine=2;assert(zu_command(cmd,sizeof(cmd),"ZZUAE-JIT","1234abcd",&c));assert(strstr(cmd," ENGINE INTERPRETER020"));
    c.engine=3;assert(!zu_valid(&c));c.engine=0;
    assert(zu_command(cmd,sizeof(cmd),"ZZUAE-Player","1234abcd",&c));assert(!strstr(cmd," ENGINE "));
    c.audio=3;assert(!zu_valid(&c));c.audio=0;
    strcpy(c.disk,"DF0:bad\nExecute something");assert(!zu_valid(&c));
    puts("PASS: settings round-trip, rejected partial/invalid settings, Shell quoting, command bounds and output selection");
}
