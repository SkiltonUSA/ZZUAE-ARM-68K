#if ZU_JIT_TRACE_INSTRUCTIONS == 1
#include "jit_timing.h"
#endif
extern unsigned zzuae_engine;
extern "C" void zzuae_jit_validate_current();
/* Included in newcpu.cpp: retain upstream event/exception/interrupt handling.
 * Count dispatches, not guest instructions, when a dispatch executes a block. */
extern "C" void zzuae_run_accelerated(unsigned limit,uint32_t *dispatches,uint32_t *cycles) {
 const unsigned start=*dispatches;
 while((*dispatches-start)<limit && (!uae_frame_limit || timeframes<uae_frame_limit) && !regs.halted) {
  const unsigned before=get_cycles();
  TRY(fault) {
   regs.pissoff=0;
   bool translate=zzuae_engine==1;
#if ZU_JIT_TRACE_INSTRUCTIONS == 1
   // Learned cycle totals are valid only for fixed-cost instructions.
   translate=translate && zzuae_constant_cycles(get_diword(0));
#endif
   if(translate) {
    // No linked-block run can hide cancellation from the host indefinitely.
    zzuae_jit_validate_current();
#if ZU_JIT_TRACE_INSTRUCTIONS == 1
    // Validation and cache reclamation are host work, not guest clock ticks.
    regs.pissoff=0;
#endif
    ((void(*)())pushall_call_handler)();
   } else {
    regs.instruction_pc=m68k_getpc();regs.opcode=get_diword(0);
    cpu_cycles=adjust_cycles(cpufunctbl[regs.opcode](regs.opcode));
    do_cycles(cpu_cycles);
   }
   check_uae_int_request();
   if(regs.spcflags && !regs.halted)do_specialties(0);
  } CATCH(fault) {bus_error();} ENDTRY
  *cycles+=(get_cycles()-before)/(CYCLE_UNIT/2);++*dispatches;
 }
}
