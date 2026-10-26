/* A600 empty-slot Gayle subset. Register conventions follow UAE4ARM gayle.cpp.
 * No IDE media or PCMCIA card backend is attached in this floppy-only port. */
static addrbank profile_gayle,profile_gayle_id;
static unsigned profile_id_bit;
static uae_u8 profile_irq_enable,profile_config,profile_cs;
static uae_u32 profile_io_bget(uaecptr addr) {
    if((addr&0xa0000)!=0xa0000)return 0;
    unsigned reg=addr&0xffff;
    if(reg==0x8000)return profile_cs; /* card detect stays clear */
    if(reg==0x9000)return 0; /* no device interrupt */
    if(reg==0xa000)return profile_irq_enable;
    if(reg==0xb000)return profile_config;
    if(reg>=0x4000)return 0;
    return (reg&0x1f)==0x1c?0x7f:0xff; /* upstream empty IDE status */
}
static void profile_io_bput(uaecptr addr,uae_u32 v) {
    if((addr&0xa0000)!=0xa0000)return;
    switch(addr&0xffff){
        case 0x8000:profile_cs=v&3;break;
        case 0xa000:profile_irq_enable=v;break;
        case 0xb000:profile_config=v&15;break;
    }
}
static uae_u32 profile_id_bget(uaecptr addr) {
    if((addr&0xffff)!=0x1000)return 0;
    unsigned bit=profile_id_bit++;
    return bit==0 || bit==1 || bit==3?0x80:0; /* serial $d0 ID */
}
static void profile_id_bput(uaecptr,uae_u32){profile_id_bit=0;}
#define PROFILE_IO_WIDTHS(n) \
static uae_u32 n##_wget(uaecptr a){return (n##_bget(a)<<8)|n##_bget(a+1);} \
static uae_u32 n##_lget(uaecptr a){return (n##_wget(a)<<16)|n##_wget(a+2);} \
static void n##_wput(uaecptr a,uae_u32 v){n##_bput(a,v>>8);n##_bput(a+1,v);} \
static void n##_lput(uaecptr a,uae_u32 v){n##_wput(a,v>>16);n##_wput(a+2,v);}
PROFILE_IO_WIDTHS(profile_io)
PROFILE_IO_WIDTHS(profile_id)
#undef PROFILE_IO_WIDTHS
static void profile_map_gayle(void) {
    profile_id_bit=profile_irq_enable=profile_config=profile_cs=0;
    profile_gayle=profile_gayle_id=dummy_bank;
    profile_gayle.flags=profile_gayle_id.flags=ABFLAG_IO;
    profile_gayle.bget=profile_io_bget;profile_gayle.wget=profile_io_wget;profile_gayle.lget=profile_io_lget;
    profile_gayle.bput=profile_io_bput;profile_gayle.wput=profile_io_wput;profile_gayle.lput=profile_io_lput;
    profile_gayle_id.bget=profile_id_bget;profile_gayle_id.wget=profile_id_wget;profile_gayle_id.lget=profile_id_lget;
    profile_gayle_id.bput=profile_id_bput;profile_gayle_id.wput=profile_id_wput;profile_gayle_id.lput=profile_id_lput;
    map_banks(&profile_gayle,0xd8,6,0);map_banks(&profile_gayle_id,0xdd,2,0);
}
