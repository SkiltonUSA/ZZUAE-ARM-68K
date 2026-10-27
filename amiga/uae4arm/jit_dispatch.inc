extern unsigned zzuae_engine;
extern "C" void zzuae_jit_validate_current();
/* Included in newcpu.cpp: retain upstream event/exception/interrupt handling.
 * Count dispatches, not guest instructions, when a dispatch executes a block. */
extern "C" void zzuae_run_accelerated(unsigned limit,uint32_t *dispatches,uint32_t *cycles) {
 const unsigned end=*dispatches+limit;
 while(*dispatches<end && timeframes<uae_frame_limit && !regs.halted) {
  const unsigned before=get_cycles();
  TRY(fault) {
   regs.pissoff=0;
   if(zzuae_engine==1) {
    // No linked-block run can hide cancellation from the host indefinitely.
    zzuae_jit_validate_current();
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
