/* Production dispatcher/reference comparison, including non-local guest faults. */
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>
#include "exception.h"
static unsigned context_count;
#undef setjmp
#define setjmp(env) (++context_count, setjmp(env))
struct Registers{unsigned opcode,instruction_pc,spcflags,halted;int pissoff;}regs;
unsigned timeframes,uae_frame_limit,cpu_cycles,zzuae_engine;
static unsigned ticks,pc,calls,faults,fault_at,fault_stage,halt_at,frame_at;
static std::vector<unsigned>trace;
const unsigned CYCLE_UNIT=512;
jmp_buf *zzuae_exception;
void zzuae_throw(int value){assert(zzuae_exception);longjmp(*zzuae_exception,value);}
unsigned get_cycles(){return ticks;}
unsigned m68k_getpc(){return pc;}
unsigned get_diword(int){return (pc>>1)&3;}
unsigned adjust_cycles(unsigned cost){return cost;}
void do_cycles(unsigned cost){ticks+=cost;trace.push_back(0x10000000|cost);}
unsigned opcode(unsigned op){
 ++calls;pc+=2;trace.push_back(0x20000000|op);
 if(calls==fault_at&&(fault_stage==1||fault_stage==3))THROW(2);
 if(calls==halt_at)regs.halted=1;
 if(calls==frame_at)timeframes=uae_frame_limit;
 regs.spcflags=calls&1;
 return (4+op)*256;
}
unsigned(*cpufunctbl[4])(unsigned)={opcode,opcode,opcode,opcode};
void translated(){do_cycles(opcode(get_diword(0)));}
void(*pushall_call_handler)()=translated;
extern "C" unsigned zzuae_jit_validate_current(){
 trace.push_back(0x50000000);
 if(calls+1==fault_at&&fault_stage==4)THROW(2);
 return 0;
}
void check_uae_int_request(){if(calls==fault_at&&fault_stage==5)THROW(2);}
void do_specialties(unsigned){
 ticks+=768;trace.push_back(0x30000000);
 if(calls==fault_at&&fault_stage==2)THROW(2);
}
void bus_error(){
 TRY(nested){++faults;ticks+=512;trace.push_back(0x40000000);if(fault_stage==3)THROW(2);}
 CATCH(nested){regs.halted=1;}ENDTRY
}
#define zzuae_run_accelerated reference_dispatch
#include "jit_dispatch.inc"
#undef zzuae_run_accelerated
#define zzuae_run_accelerated batch_dispatch
#include "jit_dispatch_batched.inc"
#undef zzuae_run_accelerated
struct Outcome{unsigned dispatched,cycles,calls,pc,frames,halted,faults,contexts;std::vector<unsigned>trace;};
static Outcome run(bool batch,unsigned engine,unsigned fault,unsigned stage,unsigned halt,unsigned frame,unsigned limit,unsigned start=0){
 regs={};timeframes=0;uae_frame_limit=3;ticks=0xfffff800;pc=calls=faults=0;
 zzuae_engine=engine;fault_at=fault;fault_stage=stage;halt_at=halt;frame_at=frame;trace.clear();context_count=0;
 uint32_t dispatched=start,cycles=0;
 (batch?batch_dispatch:reference_dispatch)(limit,&dispatched,&cycles);
 assert(!zzuae_exception);
 return {dispatched,cycles,calls,pc,timeframes,regs.halted,faults,context_count,trace};
}
int main(){
 unsigned cases=0;
 for(unsigned engine:{1u,2u})for(unsigned fault:{0u,1u,17u,255u,256u})
 for(unsigned stage:{1u,2u,3u,4u,5u})for(unsigned halt:{0u,31u})
 for(unsigned frame:{0u,63u})for(unsigned limit:{0u,1u,7u,256u}){
  auto a=run(false,engine,fault,stage,halt,frame,limit),b=run(true,engine,fault,stage,halt,frame,limit);
  assert(a.dispatched==b.dispatched&&a.cycles==b.cycles&&a.calls==b.calls&&a.pc==b.pc);
  assert(a.frames==b.frames&&a.halted==b.halted&&a.faults==b.faults&&a.trace==b.trace);++cases;
 }
 auto plain=run(false,1,0,0,0,0,256),batch=run(true,1,0,0,0,0,256);
 assert(plain.contexts==256&&batch.contexts==1);
 auto a=run(false,1,17,2,0,0,256,UINT32_MAX-100),b=run(true,1,17,2,0,0,256,UINT32_MAX-100);
 assert(a.dispatched==155&&b.dispatched==155&&a.cycles==b.cycles&&a.trace==b.trace);
 uae_frame_limit=0;uint32_t count=0,cycles=0;batch_dispatch(256,&count,&cycles);assert(count==256&&!zzuae_exception);
 printf("PASS %u JIT dispatcher/reference cases: faults, events, halt, frame/count bounds and wrap\n",cases);
}
