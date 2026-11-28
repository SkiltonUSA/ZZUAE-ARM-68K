#include "launcher_config.h"
#include <assert.h>
int main(void){
    struct zu_config c={.rom="DH0:ROMs/Kick12.rom",.disk="DH0:Games/Some *$`\" disk.adf",.writes=1,.limit=2,.fps=2,.profile=1,.joystick=1,.testing=1},d=c;
    for(unsigned model=0;model<5;model++){
        struct zu_config m={.rom="ROMs/kick.rom",.profile=model,.engine=2,.ram=4};
        for(unsigned size=2;size<=4;size++){m.ram=size;assert(zu_valid(&m)&&zu_fast_engine(&m));}
        m.engine=0;assert(zu_valid(&m)==(model!=ZP_A1200));
        m.engine=1;assert(!zu_valid(&m));m.engine=3;assert(!zu_valid(&m));
        m.engine=2;m.fpu=1;assert(!zu_valid(&m));
        for(unsigned ram=0;ram<5;ram++)assert(zu_ram_setting(model,zu_ram_choice(model,ram))==(model==ZP_A1200&&ram==1?0:ram));
    }
    char cmd[4096],small[8];FILE *f;
    assert(c.fps==2);
    assert(c.pcm==0);
    assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," RATE 22050"));
    c.pcm=2;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," RATE 0"));
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d)&&d.pcm==2);fclose(f);
    c.pcm=1;assert(zu_command(cmd,sizeof(cmd),"player","1234abcd",&c));assert(strstr(cmd," RATE 27000"));
    c.pcm=3;assert(!zu_valid(&c));c.pcm=0;
    f=tmpfile();assert(f);fputs("pcm=3\n",f);rewind(f);assert(!zu_load(f,&d)&&d.pcm==2);fclose(f);

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
    assert(!strcmp(zu_player(&c),"ZZUAE-JIT"));
    c.engine=3;assert(zu_valid(&c));assert(!zu_engine_fpu(c.engine));
    assert(!strcmp(zu_player(&c),"ZZUAE-Cyclone"));
    assert(zu_command(cmd,sizeof(cmd),zu_player(&c),"1234abcd",&c));
    assert(strstr(cmd,"ZZUAE-Cyclone")&&!strstr(cmd," ENGINE ")&&!strstr(cmd," FPU "));
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d)&&d.engine==3);fclose(f);
    c.fpu=1;assert(!zu_valid(&c));assert(!zu_command(cmd,sizeof(cmd),zu_player(&c),"1234abcd",&c));
    c.engine=1;assert(zu_valid(&c)&&!strcmp(zu_player(&c),"ZZUAE-FPU"));
    c.fpu=0;c.engine=4;assert(!zu_valid(&c));c.engine=0;
    assert(!strcmp(zu_player(&c),"ZZUAE-Player"));
    assert(zu_command(cmd,sizeof(cmd),"ZZUAE-Player","1234abcd",&c));assert(!strstr(cmd," ENGINE "));
    c.profile=ZP_A600;c.ram=4;c.engine=2;
    assert(zu_valid(&c)&&zu_storage_engine(&c));
    strcpy(c.hdf,"USBSD:2");c.disk[0]=0;c.writes=0;
    assert(zu_command(cmd,sizeof(cmd),zu_player(&c),"1234abcd",&c));
    assert(strstr(cmd," RAM FAST8")&&strstr(cmd," ENGINE INTERPRETER020")&&strstr(cmd,"USBSD:2"));
    f=tmpfile();assert(f);assert(zu_save(f,&c));rewind(f);assert(zu_load(f,&d)&&d.ram==4&&d.engine==2);fclose(f);
    c.engine=1;assert(!zu_valid(&c)&&!zu_storage_engine(&c));
    c.engine=3;assert(!zu_valid(&c)&&!zu_storage_engine(&c));
    c.engine=2;c.fpu=1;assert(!zu_valid(&c)&&!zu_storage_engine(&c));
    c.engine=0;c.fpu=0;assert(zu_valid(&c));
    d=c;d.profile=ZP_A1200;d.ram=1;d.engine=2;d.writes=0;
    assert(zu_valid(&d)&&zu_storage_engine(&d));
    assert(zu_command(cmd,sizeof cmd,zu_player(&d),"1234abcd",&d));
    assert(strstr(cmd," MODEL A1200")&&strstr(cmd," ENGINE INTERPRETER020")&&strstr(cmd," HDF \"USBSD:2\""));
    d.writes=1;assert(!zu_valid(&d));d.writes=2;assert(!zu_valid(&d));d.writes=0;
    d.engine=1;assert(!zu_valid(&d)&&!zu_storage_engine(&d));d.engine=0;assert(!zu_valid(&d));
    d.engine=2;d.fpu=1;assert(!zu_valid(&d));d.fpu=0;
    d.hdfbus=1;
    strcpy(d.hdf,"RAM:CF image.img");
    assert(zu_command(cmd,sizeof cmd,zu_player(&d),"1234abcd",&d));
    assert(strstr(cmd," PCMCIA \"RAM:CF image.img\""));
    f=tmpfile();assert(f);assert(zu_save(f,&d));rewind(f);
    struct zu_config card=d;card.hdfbus=0;assert(zu_load(f,&card)&&card.hdfbus==1);fclose(f);
    d.engine=1;assert(!zu_valid(&d));d.engine=2;
    d.fpu=1;assert(!zu_valid(&d));d.fpu=0;
    d.hdfbus=2;assert(!zu_valid(&d));d.hdfbus=1;
    strcpy(d.hdf,"USBSD:2");assert(!zu_valid(&d));
    c.audio=3;assert(!zu_valid(&c));c.audio=0;
    strcpy(c.disk,"DF0:bad\nExecute something");assert(!zu_valid(&c));
    puts("PASS: settings round-trip, rejected partial/invalid settings, Shell quoting, command bounds and output selection");
}
