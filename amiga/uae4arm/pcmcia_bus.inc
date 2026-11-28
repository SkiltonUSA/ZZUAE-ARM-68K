/* Optional single-card CF/ATA adapter. The image is attached to either Gayle
 * IDE or PCMCIA, never both. The storage transport and write policy are shared. */
#include "pcmcia_ata.h"
static struct zu_pcmcia zu_card;
static addrbank zu_card_bank;
static unsigned zu_card_cs_mask;
static unsigned zu_card_read(void *,unsigned reg){
    return reg==ZU_PC_DATA?ide_get_data(zu_ide_selected()):ide_read_reg(zu_ide_selected(),reg);
}
static void zu_card_write(void *,unsigned reg,unsigned value){
    if(reg==ZU_PC_DATA)ide_put_data(zu_ide_selected(),value);
    else ide_write_reg(zu_ide_selected(),reg,value);
}
static const struct zu_pcmcia_io zu_card_io={NULL,zu_card_read,zu_card_write};
static uae_u32 zu_card_bget(uaecptr a){return zu_pcmcia_read8(&zu_card,&zu_card_io,a);}
static uae_u32 zu_card_wget(uaecptr a){return zu_pcmcia_read16(&zu_card,&zu_card_io,a);}
static uae_u32 zu_card_lget(uaecptr a){uae_u32 hi=zu_card_wget(a);return (hi<<16)|zu_card_wget(a+2);}
static void zu_card_bput(uaecptr a,uae_u32 v){zu_pcmcia_write8(&zu_card,&zu_card_io,a,v);}
static void zu_card_wput(uaecptr a,uae_u32 v){zu_pcmcia_write16(&zu_card,&zu_card_io,a,v);}
static void zu_card_lput(uaecptr a,uae_u32 v){zu_card_wput(a,v>>16);zu_card_wput(a+2,v);}
static unsigned zu_card_cs(){
    unsigned bits=zu_card.present&&!zu_card.disabled?0x40:0;
    if(bits && !zu_ide[0]->hdhfd.hfd.ci.readonly)bits|=8;
    if(bits && zu_card.configured && ide_irq_check(zu_ide[0],false))bits|=4;
    return bits|zu_card_cs_mask|profile_cs;
}
static void zu_card_control(unsigned value){
    unsigned disabled=value&1;
    zu_card_cs_mask=value&0xfcu;profile_cs=value&3;
    if(disabled!=zu_card.disabled && zu_card.present)zu_ide_irq|=0x40;
    zu_card.disabled=disabled;
}
static void zu_card_rethink(){
    if(zu_card.present&&!zu_card.disabled && zu_card.configured && ide_irq_check(zu_ide[0],false))zu_ide_irq|=4;
    unsigned pending=zu_ide_irq&profile_irq_enable;
    if((pending&0x40) || ((pending&4)&&(profile_irq_enable&1))){
        if(!(intreq&0x2000))INTREQ_0(0xa000);
    }
    if((pending&4)&&!(profile_irq_enable&1)&&!(intreq&8))INTREQ_0(0x8008);
}
static void zu_card_init(){
    memset(&zu_card,0,sizeof zu_card);zu_card_cs_mask=0;
    zu_card.present=zu_ide[0]->hdhfd.size!=0;zu_pcmcia_reset(&zu_card);
    profile_config=8;zu_ide_irq=zu_card.present?0x40:0;
    zu_card_bank=dummy_bank;zu_card_bank.flags=ABFLAG_IO;
    zu_card_bank.bget=zu_card_bget;zu_card_bank.wget=zu_card_wget;zu_card_bank.lget=zu_card_lget;
    zu_card_bank.bput=zu_card_bput;zu_card_bank.wput=zu_card_wput;zu_card_bank.lput=zu_card_lput;
    map_banks(&zu_card_bank,0xa0,8,0);
}
