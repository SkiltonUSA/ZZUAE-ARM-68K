#include "fast_memory.h"
static addrbank zu_fast_bank,zu_fast_config;
static unsigned zu_fast_low;
static bool zu_fast_pending;
static uae_u32 REGPARAM2 zu_fast_bget(uaecptr a){return zu_fast_bank.baseaddr[(a-zu_fast_bank.start)&zu_fast_bank.mask];}
static void REGPARAM2 zu_fast_bput(uaecptr a,uae_u32 v){zu_fast_bank.baseaddr[(a-zu_fast_bank.start)&zu_fast_bank.mask]=v;}
static uae_u32 REGPARAM2 zu_fast_wget(uaecptr a){return (zu_fast_bget(a)<<8)|zu_fast_bget(a+1);}
static uae_u32 REGPARAM2 zu_fast_lget(uaecptr a){return (zu_fast_wget(a)<<16)|zu_fast_wget(a+2);}
static void REGPARAM2 zu_fast_wput(uaecptr a,uae_u32 v){zu_fast_bput(a,v>>8);zu_fast_bput(a+1,v);}
static void REGPARAM2 zu_fast_lput(uaecptr a,uae_u32 v){zu_fast_wput(a,v>>16);zu_fast_wput(a+2,v);}
static int REGPARAM2 zu_fast_check(uaecptr a,uae_u32 n){unsigned o=a-zu_fast_bank.start;return o<=zu_fast_bank.reserved_size&&n<=zu_fast_bank.reserved_size-o;}
static uae_u8 *REGPARAM2 zu_fast_xlate(uaecptr a){return zu_fast_bank.baseaddr+((a-zu_fast_bank.start)&zu_fast_bank.mask);}
static uae_u32 REGPARAM2 zu_fc_bget(uaecptr a){return zu_fast_pending?zu_fast_config_byte(zu_fast_bank.reserved_size,a&0xffff):0xff;}
static uae_u32 REGPARAM2 zu_fc_wget(uaecptr a){return (zu_fc_bget(a)<<8)|zu_fc_bget(a+1);}
static uae_u32 REGPARAM2 zu_fc_lget(uaecptr a){return (zu_fc_wget(a)<<16)|zu_fc_wget(a+2);}
static void REGPARAM2 zu_fc_bput(uaecptr a,uae_u32 v){
 if(!zu_fast_pending)return;
 switch(a&0xffff){
 case 0x4a:zu_fast_low=v&0xf0;break;
 case 0x48:{
  unsigned start=((v&0xff)|(zu_fast_low>>4))<<16;
  if(start<0x200000 || start>0xa00000-zu_fast_bank.reserved_size)return;
  zu_fast_bank.start=start;map_banks(&zu_fast_bank,start>>16,zu_fast_bank.reserved_size>>16,0);
  zu_fast_pending=false;map_banks(&dummy_bank,0xe8,1,0);break;
 }
 case 0x4c:zu_fast_pending=false;map_banks(&dummy_bank,0xe8,1,0);break;
 }
}
static void REGPARAM2 zu_fc_wput(uaecptr a,uae_u32 v){zu_fc_bput(a,v>>8);zu_fc_bput(a+1,v);}
static void REGPARAM2 zu_fc_lput(uaecptr a,uae_u32 v){zu_fc_wput(a,v>>16);zu_fc_wput(a+2,v);}
static void zu_fast_init(){
 unsigned size=currprefs.fastmem[0].size;
 if(!size)return;
 if(zu_fast_bank.baseaddr)mapped_free(&zu_fast_bank);
 zu_fast_bank=dummy_bank;zu_fast_bank.flags=ABFLAG_RAM;
 zu_fast_bank.reserved_size=size;zu_fast_bank.mask=size-1;zu_fast_bank.start=0x200000;
 if(!mapped_malloc(&zu_fast_bank))abort();
 zu_fast_bank.bget=zu_fast_bget;zu_fast_bank.wget=zu_fast_wget;zu_fast_bank.lget=zu_fast_lget;
 zu_fast_bank.bput=zu_fast_bput;zu_fast_bank.wput=zu_fast_wput;zu_fast_bank.lput=zu_fast_lput;
 zu_fast_bank.wgeti=zu_fast_wget;zu_fast_bank.lgeti=zu_fast_lget;
 zu_fast_bank.check=zu_fast_check;zu_fast_bank.xlateaddr=zu_fast_xlate;
 /* Exercise every bank and expansion edge before exposing it to the guest. */
 for(unsigned o=0;o<size;o+=65536){zu_fast_lput(0x200000+o,o^0x12345678);zu_fast_lput(0x20fffc+o,o^0x89abcdef);}
 for(unsigned o=0;o<size;o+=65536)if(zu_fast_lget(0x200000+o)!=(o^0x12345678u)||zu_fast_lget(0x20fffc+o)!=(o^0x89abcdefu))abort();
 memset(zu_fast_bank.baseaddr,0,size);
 zu_fast_config=dummy_bank;zu_fast_config.flags=ABFLAG_IO;
 zu_fast_config.bget=zu_fc_bget;zu_fast_config.wget=zu_fc_wget;zu_fast_config.lget=zu_fc_lget;
 zu_fast_config.bput=zu_fc_bput;zu_fast_config.wput=zu_fc_wput;zu_fast_config.lput=zu_fc_lput;
 zu_fast_pending=true;zu_fast_low=0;map_banks(&zu_fast_config,0xe8,1,0);
}
