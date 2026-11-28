#include "pcmcia_ata.h"
#include <assert.h>
#include <stdio.h>
struct ata {unsigned reads,writes,reg,value;};
static unsigned read_reg(void *p,unsigned r){struct ata*a=p;a->reads++;a->reg=r;return r?0x58:0x1234;}
static void write_reg(void*p,unsigned r,unsigned v){struct ata*a=p;a->writes++;a->reg=r;a->value=v;}
int main(void){
    struct zu_pcmcia c={0};struct ata a={0};struct zu_pcmcia_io io={&a,read_reg,write_reg};
    assert(!zu_pcmcia_read16(&c,&io,0));
    zu_pcmcia_write16(&c,&io,0x20008,0xffff);assert(!a.writes);
    c.present=1;zu_pcmcia_reset(&c);
    /* Walk complete CIS tuples as card.resource does, not just known offsets. */
    unsigned at=0,tuples=0;
    while(zu_pcmcia_read8(&c,&io,at*2)!=255){
        unsigned n=zu_pcmcia_read8(&c,&io,(at+1)*2);at+=n+2;tuples++;
        assert(at<sizeof zu_pcmcia_cis);
    }
    assert(tuples==10 && at==sizeof zu_pcmcia_cis-1);
    assert(zu_pcmcia_register(&c,0x20008)==-1);
    zu_pcmcia_write8(&c,&io,0x200,1);
    assert(zu_pcmcia_read8(&c,&io,0x201)==1);
    assert(zu_pcmcia_read16(&c,&io,0x20008)==0x1234 && a.reads==1);
    assert(zu_pcmcia_read8(&c,&io,0x20008)==0x12 && a.reads==2);
    assert(zu_pcmcia_read8(&c,&io,0x30008)==0x34 && a.reads==2);
    zu_pcmcia_write8(&c,&io,0x30008,0xab);assert(!a.writes);
    zu_pcmcia_write8(&c,&io,0x20008,0xcd);assert(a.writes==1 && a.value==0xabcd);
    zu_pcmcia_write16(&c,&io,0x20008,0x5678);assert(a.writes==2 && a.value==0x5678);
    assert(zu_pcmcia_register(&c,0x2000e)==ZU_PC_CONTROL);
    zu_pcmcia_write8(&c,&io,0x200,2);
    assert(zu_pcmcia_register(&c,0x20008)==-1);
    assert(zu_pcmcia_read16(&c,&io,0x201f0)==0x1234 && a.reads==3);
    assert(zu_pcmcia_read8(&c,&io,0x301f6)==0x58 && a.reg==7);
    assert(zu_pcmcia_register(&c,0x203f6)==ZU_PC_CONTROL);
    assert(zu_pcmcia_register(&c,0x203f7)==ZU_PC_ADDRESS);
    zu_pcmcia_write8(&c,&io,0x200,3);assert(!c.configured);
    zu_pcmcia_write8(&c,&io,0x200,1);c.disabled=1;
    assert(!zu_pcmcia_read16(&c,&io,0x20008));assert(!zu_pcmcia_read8(&c,&io,0));
    c.disabled=0;zu_pcmcia_write8(&c,&io,0x40000,0);assert(!c.configured && !c.config[0]);
    zu_pcmcia_write8(&c,&io,0x200,0x81);assert(!c.configured && !c.latch);
    puts("PASS PCMCIA ATA: CIS walk, configuration, linear/PC IO, odd-byte aliases, exact word transfers, reset and absent/disabled card");
}
