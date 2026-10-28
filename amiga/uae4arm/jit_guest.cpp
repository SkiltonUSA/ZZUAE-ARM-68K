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
extern "C" void zzuae_jit_validate_current();
extern "C" void zzuae_jit_test_tail();
extern "C" void zz_jit_fault_restore();
extern void reset_all_systems();
extern unsigned zz_jit_translated,zz_jit_fallback;
extern cpuop_func *cpufunctbl[65536];
static unsigned char heap[0x800000] __attribute__((aligned(64)));
static unsigned fixture_address=0x2000,io_calls;
static uae_u32 test_lget(uaecptr a){++io_calls;return chipmem_bank.lget(a&0xffff);}
static uae_u32 test_wget(uaecptr a){++io_calls;return chipmem_bank.wget(a&0xffff);}
static uae_u32 test_bget(uaecptr a){++io_calls;return chipmem_bank.bget(a&0xffff);}
static void test_lput(uaecptr a,uae_u32 v){++io_calls;chipmem_bank.lput(a&0xffff,v);}
static void test_wput(uaecptr a,uae_u32 v){++io_calls;chipmem_bank.wput(a&0xffff,v);}
static void test_bput(uaecptr a,uae_u32 v){++io_calls;chipmem_bank.bput(a&0xffff,v);}
static addrbank test_bank;
static void diagnostic(unsigned phase){if(uae_shared){ad_put(uae_shared,0x480940u,phase);__asm__ volatile("dsb sy":::"memory");}}
static void reset_fixture(unsigned seed){
 uintptr tags=regs.cache_tags;
 memset(&regs,0,sizeof(regs));regs.s=1;regs.intmask=7;regs.regs[15]=0x70000;
 regs.regs[0]=seed;regs.regs[1]=(seed&255)|3;regs.regs[2]=0x12345678;
 regs.regs[8]=fixture_address;regs.regs[9]=fixture_address+64;
 regs.ccrflags.x=seed&0x20000000u;
 regs.mem_banks=(uintptr)mem_banks;regs.cache_tags=tags;
 m68k_setpc(0x100);regs.pissoff=-1;
 for(unsigned i=0;i<256;i++){put_byte(0x2000+i,i^seed);put_byte(0x6ff00+i,i+seed);}
 for(unsigned i=0;i<128;i++)put_byte(fixture_address+i,i^seed);
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
static const uint16_t bytes[]={0x1080,0x1410,0x10c1,0x1618,0x1802,0x1a3c,0x0080,0x60fe};
struct Fixture {const uint16_t *code;unsigned words,instructions;};
#define FIX(a,n) {a,sizeof(a)/2,n}
static const Fixture fixtures[]={FIX(arithmetic,6),FIX(flags,5),FIX(memory,6),FIX(divide_u,4),FIX(divide_s,3),FIX(branch,2),FIX(movem,3),FIX(shifts,4),FIX(arithmetic,6),FIX(bytes,7),
 FIX(memory,6),FIX(memory,6),FIX(memory,6),FIX(memory,6),FIX(memory,6),FIX(memory,6),FIX(memory,6),FIX(memory,6)};
static const unsigned memory_addresses[]={0x12000,0x2001,0xc02000,0xfc2000,0xe02000,0xfffe,0x12002000,0x22000};
extern "C" int mesen_test(int verify,MesenResult *r,int(*stop)(),uint32_t(*clock)()){
 memset(r,0,sizeof(*r));int fatal=setjmp(uae_fatal);if(fatal){zz_jit_fault_restore();uae_fatal_active=0;r->errors=fatal;return 1;}uae_fatal_active=1;
 if(!zz_jit_fault_install()){uae_fatal_active=0;r->errors=98;return 1;}diagnostic(1);fb_heap_init(heap,sizeof(heap));memset(&currprefs,0,sizeof(currprefs));
 currprefs.cpu_model=68020;currprefs.cachesize=ZU_JIT_CACHE_KIB;currprefs.address_space_24=true;
 currprefs.chipmem_size=0x100000;currprefs.bogomem_size=0x80000;changed_prefs=currprefs;
 diagnostic(2);memory_init();diagnostic(3);reset_all_systems();
 if(ZU_JIT_CACHE_KIB==32768 && zzuae_jit_cache_selftest())abort();
 diagnostic(4);init_m68k();diagnostic(5);map_overlay(1);diagnostic(6);do_cycles=cycles;set_cache_state(1);diagnostic(7);
 unsigned start=clock();diagnostic(8);
 const unsigned seeds[]={0,0xffffffff,0x7fffffff,0x80000000,0x12345678,0x00010000,0xffff0000,0x20000000};
 for(unsigned test=0;test<sizeof(fixtures)/sizeof(fixtures[0]);test++){
  fixture_address=test<10?0x2000:memory_addresses[test-10];
  const Fixture &f=fixtures[test];
  for(unsigned i=0;i<f.words;i++)put_word(0x100+i*2,f.code[i]);
  flush_icache_hard(3);
  if(ZU_JIT_CACHE_KIB==32768 && (test==0 || test==2))zzuae_jit_test_tail();
  for(unsigned round=0;round<24;round++){
   // Change the mapping after this same block has been translated. Device
   // callbacks have observable side effects and must never become RAM loads.
   if(test==17 && round==12){
    test_bank=chipmem_bank;test_bank.flags=ABFLAG_IO;
    test_bank.lget=test_lget;test_bank.wget=test_wget;test_bank.bget=test_bget;
    test_bank.lput=test_lput;test_bank.wput=test_wput;test_bank.bput=test_bput;
    // Deliberately bypass map_banks' normal cache flush for this stronger test.
    mem_banks[2]=&test_bank;
   }
   if(stop()){compiler_exit();zz_jit_fault_restore();uae_fatal_active=0;return 2;}
   // Modify an already-translated immediate; checksum invalidation must rebuild it.
   if(test==8 && round==12){put_word(0x100,0x7009);}
   unsigned seed=seeds[round%8];diagnostic(0x10000000u|(test<<16)|(round<<8)|1);reset_fixture(seed);io_calls=0;reference(f.instructions);
   unsigned expected_calls=io_calls;
   regstruct expected=regs;unsigned expected_pc=m68k_getpc();
   unsigned char ram[512];
   for(unsigned i=0;i<256;i++){ram[i]=get_byte(0x2000+i);ram[i+256]=get_byte(0x6ff00+i);}
   unsigned char target[128];for(unsigned i=0;i<128;i++)target[i]=get_byte(fixture_address+i);
   reset_fixture(seed);io_calls=0;diagnostic(0x10000000u|(test<<16)|(round<<8)|2);
#if ZU_JIT_EVENT_BLOCKS
   for(unsigned n=0;n<64 && m68k_getpc()!=expected_pc;n++){
#else
   for(unsigned n=0;n<(ZU_JIT_TRACE_INSTRUCTIONS==1?f.instructions:1);n++){
#endif
    zzuae_jit_validate_current();((void(*)())pushall_call_handler)();
   }
   diagnostic(0x10000000u|(test<<16)|(round<<8)|3);
   unsigned mismatch=0;
   if(io_calls!=expected_calls)mismatch|=1u<<20;
   for(unsigned i=0;i<128;i++)if(target[i]!=get_byte(fixture_address+i))mismatch|=1u<<21;
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
