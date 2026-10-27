/* Test the production batching wrapper with faulting instruction/event handlers.
 * Actual UAE opcode/Chip RAM equivalence is covered by check_machine.py. */
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>
#include "exception.h"
#include "machine.h"
struct Registers { unsigned opcode,ir,instruction_pc,spcflags,halted; } regs;
unsigned timeframes,uae_frame_limit,cpu_cycles;
static unsigned calls,pc,fault_at,fault_stage,halt_at,frame_at,faults;
static std::vector<unsigned> trace;
const unsigned CYCLE_UNIT=512;
jmp_buf *zzuae_exception;
void zzuae_throw(int value){assert(zzuae_exception);longjmp(*zzuae_exception,value);}
unsigned m68k_getpc(){return pc;}
void do_cycles(unsigned cost){trace.push_back(0x10000000|cost);}
unsigned adjust_cycles(unsigned cost){return cost+256;}
unsigned opcode(unsigned op){
 ++calls;trace.push_back(0x20000000|op);pc+=2;
 if(calls==fault_at && (fault_stage==1 || fault_stage==3))THROW(2);
 if(calls==frame_at)timeframes=uae_frame_limit;
 if(calls==halt_at)regs.halted=1;
 regs.ir=(regs.ir+1)&3;regs.spcflags=calls&1;
 return (4+op)*256;
}
unsigned (*cpufunctbl[4])(unsigned)={opcode,opcode,opcode,opcode};
void do_specialties(unsigned cost){
 trace.push_back(0x30000000|cost);
 if(calls==fault_at && fault_stage==2)THROW(2);
}
void bus_error(){
 /* Model the real handler's nested TRY / double-fault-to-halt behaviour. */
 TRY(nested) {++faults;trace.push_back(0x40000000);if(fault_stage==3)THROW(2);}
 CATCH(nested) {regs.halted=1;} ENDTRY
}
#include "cpu_batch.inc"
struct Outcome { unsigned checked,cycles,calls,pc,ir,frames,halted,faults;std::vector<unsigned> trace; };
static Outcome run(bool batch,unsigned fault,unsigned stage,unsigned halt,unsigned frame,unsigned limit){
 regs={};timeframes=0;uae_frame_limit=3;cpu_cycles=512;calls=pc=faults=0;
 fault_at=fault;fault_stage=stage;halt_at=halt;frame_at=frame;trace.clear();
 uint32_t checked=0,cycles=0;
 if(batch)zzuae_run_batch(limit,&checked,&cycles);
 else while(checked<limit && timeframes<uae_frame_limit && !regs.halted){cycles+=zzuae_step();checked++;}
 assert(!zzuae_exception);
 return {checked,cycles,calls,pc,regs.ir,timeframes,regs.halted,faults,trace};
}
int main(){
 for(unsigned fault: {0u,1u,17u,255u,256u})
 for(unsigned stage: {1u,2u,3u})
 for(unsigned halt: {0u,31u})
 for(unsigned frame: {0u,63u})
 for(unsigned limit: {0u,1u,7u,256u}){
  auto a=run(false,fault,stage,halt,frame,limit),b=run(true,fault,stage,halt,frame,limit);
  assert(a.checked==b.checked && a.cycles==b.cycles && a.calls==b.calls);
  assert(a.pc==b.pc && a.ir==b.ir && a.frames==b.frames && a.halted==b.halted && a.faults==b.faults);
  assert(a.trace==b.trace);
 }
 /* A fault in the nested handler must restore its outer exception context. */
 regs.halted=0;fault_stage=3;bus_error();assert(regs.halted && !zzuae_exception);
 puts("PASS: CPU batch/reference instruction and cycle traces, faults, specials, halt, frame and instruction bounds");
}
