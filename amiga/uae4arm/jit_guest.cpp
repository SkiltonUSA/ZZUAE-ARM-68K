/* Bounded upstream guest-JIT differential diagnostic; not a game player. */
#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "memory.h"
#include "custom.h"
#include "newcpu.h"
#include "events.h"
#include "bench.h"
#include "machine.h"
#include "jit_cache.h"
#include "protocol.h"
#include <setjmp.h>
extern "C" { extern jmp_buf uae_fatal;extern int uae_fatal_active;void fb_heap_init(void*,size_t); }
extern "C" int zz_jit_fault_install();
extern "C" void zz_jit_fault_restore();
extern void reset_all_systems();
extern unsigned zz_jit_translated,zz_jit_fallback;
extern cpuop_func *cpufunctbl[65536];
static unsigned char heap[0x800000] __attribute__((aligned(64)));
static void diagnostic(unsigned phase){if(uae_shared){ad_put(uae_shared,0x480940u,phase);__asm__ volatile("dsb sy":::"memory");}}
static void reset_fixture(unsigned seed){
 uintptr tags=regs.cache_tags;
 memset(&regs,0,sizeof(regs));regs.s=1;regs.intmask=7;regs.regs[15]=0x70000;
 regs.regs[0]=seed;regs.regs[1]=(seed&255)|3;regs.regs[2]=0x12345678;
 regs.regs[8]=0x2000;regs.regs[9]=0x2040;
 regs.ccrflags.x=seed&0x20000000u;
 regs.mem_banks=(uintptr)mem_banks;regs.cache_tags=tags;
 m68k_setpc(0x100);regs.pissoff=-1;
 for(unsigned i=0;i<256;i++){put_byte(0x2000+i,i^seed);put_byte(0x6ff00+i,i+seed);}
}
static void reference(unsigned count){for(unsigned i=0;i<count;i++){uae_u32 op=get_diword(0);cpufunctbl[op](op);}}
static void cycles(uae_u32){} /* CPU-only differential fixture; no chipset timing claim. */
static const uint16_t arithmetic[]={0x7007,0x7203,0xd081,0x5380,0x0a80,0x1234,0x5678,0x60fe};
static const uint16_t flags[]={0xd081,0xd181,0x9280,0x57c3,0x60fe};
static const uint16_t memory[]={0x2080,0x3141,4,0x2410,0xb580,0x20c0,0x60fe};
static const uint16_t divide_u[]={0xc0c1,0x80c1,0x5282,0x60fe};
static const uint16_t divide_s[]={0x81c1,0x5282,0x60fe};
static const uint16_t branch[]={0x4a80,0x6704,0x5281,0x6002,0x5381,0x60fe};
static const uint16_t movem[]={0x48e7,0xf0c0,0x4cdf,0x0cf0,0x60fe};
static const uint16_t shifts[]={0xe388,0xe2a8,0xe198,0x60fe};
struct Fixture {const uint16_t *code;unsigned words,instructions;};
#define FIX(a,n) {a,sizeof(a)/2,n}
static const Fixture fixtures[]={FIX(arithmetic,6),FIX(flags,5),FIX(memory,6),FIX(divide_u,4),FIX(divide_s,3),FIX(branch,2),FIX(movem,3),FIX(shifts,4),FIX(arithmetic,6)};
extern "C" int mesen_test(int verify,MesenResult *r,int(*stop)(),uint32_t(*clock)()){
 memset(r,0,sizeof(*r));int fatal=setjmp(uae_fatal);if(fatal){zz_jit_fault_restore();uae_fatal_active=0;r->errors=fatal;return 1;}uae_fatal_active=1;
 if(!zz_jit_fault_install()){r->errors=98;return 1;}diagnostic(1);fb_heap_init(heap,sizeof(heap));memset(&currprefs,0,sizeof(currprefs));
 currprefs.cpu_model=68020;currprefs.cachesize=512;currprefs.address_space_24=true;
 currprefs.chipmem_size=0x100000;changed_prefs=currprefs;
 diagnostic(2);memory_init();diagnostic(3);reset_all_systems();diagnostic(4);init_m68k();diagnostic(5);map_overlay(1);diagnostic(6);do_cycles=cycles;set_cache_state(1);diagnostic(7);
 unsigned start=clock();diagnostic(8);
 const unsigned seeds[]={0,0xffffffff,0x7fffffff,0x80000000,0x12345678,0x00010000,0xffff0000,0x20000000};
 for(unsigned test=0;test<sizeof(fixtures)/sizeof(fixtures[0]);test++){
  const Fixture &f=fixtures[test];
  for(unsigned i=0;i<f.words;i++)put_word(0x100+i*2,f.code[i]);
  flush_icache_hard(3);
  for(unsigned round=0;round<24;round++){
   if(stop()){compiler_exit();zz_jit_fault_restore();uae_fatal_active=0;return 2;}
   // Modify an already-translated immediate; checksum invalidation must rebuild it.
   if(test==8 && round==12){put_word(0x100,0x7009);flush_icache(1);}
   unsigned seed=seeds[round%8];diagnostic(0x10000000u|(test<<16)|(round<<8)|1);reset_fixture(seed);reference(f.instructions);
   regstruct expected=regs;unsigned expected_pc=m68k_getpc();
   unsigned char ram[512];
   for(unsigned i=0;i<256;i++){ram[i]=get_byte(0x2000+i);ram[i+256]=get_byte(0x6ff00+i);}
   reset_fixture(seed);diagnostic(0x10000000u|(test<<16)|(round<<8)|2);((void(*)())pushall_call_handler)();diagnostic(0x10000000u|(test<<16)|(round<<8)|3);
   unsigned mismatch=0;
   for(unsigned i=0;i<16;i++)if(regs.regs[i]!=expected.regs[i])mismatch|=1u<<i;
   if((regs.ccrflags.nzcv^expected.ccrflags.nzcv)&0xf0000000u)mismatch|=1u<<16;
   if(regs.ccrflags.x!=expected.ccrflags.x)mismatch|=1u<<17;
   if(m68k_getpc()!=expected_pc)mismatch|=1u<<18;
   for(unsigned i=0;i<256;i++)if(ram[i]!=get_byte(0x2000+i) || ram[i+256]!=get_byte(0x6ff00+i))mismatch|=1u<<19;
   if(mismatch){r->errors=1+test*24+round;r->mismatch=mismatch;r->expected_pc=expected_pc;goto finished;}
   r->checked++;r->hash=r->hash*31+regs.regs[0]+m68k_getpc();
  }
 }
finished:
 r->ticks=clock()-start;r->actual_regs=zz_jit_translated;r->cycles=zz_jit_fallback;r->actual_pc=m68k_getpc();
 diagnostic(0xeeee);compiler_exit();diagnostic(0xffff);zz_jit_fault_restore();uae_fatal_active=0;(void)verify;return r->errors?1:0;
}
/* This CPU-only fixture has no guest FPU. Unexpected FP opcodes are a failed
 * test, never successful no-ops. Full guest exception integration is separate. */
void fpuop_arithmetic(uae_u32,uae_u16){abort();}
void fpuop_scc(uae_u32,uae_u16){abort();}
void fpuop_dbcc(uae_u32,uae_u16){abort();}
void fpuop_trapcc(uae_u32,uaecptr,uae_u16){abort();}
void fpuop_bcc(uae_u32,uaecptr,uae_u32){abort();}
void fpuop_save(uae_u32){abort();}
void fpuop_restore(uae_u32){abort();}
