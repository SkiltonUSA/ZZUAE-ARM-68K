/* Included in upstream newcpu.cpp so execution uses its private cycle state.
 * Keep the single-step reference for diagnostic comparisons. No guest opcode,
 * prefetch, interrupt or chipset scheduling is changed by the batching. */
#include "machine.h"
extern "C" unsigned zzuae_step(void) {
 volatile unsigned result=0;
 TRY (fault) {
  regs.opcode=regs.ir;do_cycles(cpu_cycles);regs.instruction_pc=m68k_getpc();
  cpu_cycles=cpufunctbl[regs.opcode](regs.opcode);cpu_cycles=adjust_cycles(cpu_cycles);
  result=cpu_cycles/(CYCLE_UNIT/2);
  if(regs.spcflags)do_specialties(cpu_cycles);
 } CATCH(fault) { bus_error(); } ENDTRY
 return result;
}

extern "C" void zzuae_run_batch(unsigned limit,uint32_t *checked,uint32_t *cycles) {
 const unsigned end=(*checked)+limit;
 /* Accounting lives outside this setjmp frame. The in-progress instruction's
  * cost must survive a fault during do_specialties; zero if the opcode faults.
  * The exception handler restores the outer context before bus_error(). */
 volatile unsigned cost=0;
 while((*checked)<end && timeframes<uae_frame_limit && !regs.halted) {
  TRY(fault) {
   while((*checked)<end && timeframes<uae_frame_limit && !regs.halted) {
    cost=0;
    regs.opcode=regs.ir;do_cycles(cpu_cycles);regs.instruction_pc=m68k_getpc();
    cpu_cycles=cpufunctbl[regs.opcode](regs.opcode);cpu_cycles=adjust_cycles(cpu_cycles);
    cost=cpu_cycles/(CYCLE_UNIT/2);
    if(regs.spcflags)do_specialties(cpu_cycles);
    (*cycles)+=cost;(*checked)++;
   }
  } CATCH(fault) {
   bus_error();(*cycles)+=cost;(*checked)++;
  } ENDTRY
 }
}
