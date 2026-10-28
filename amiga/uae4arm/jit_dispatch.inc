#if ZU_JIT_TRACE_INSTRUCTIONS == 1 || ZU_JIT_EVENT_BLOCKS
#include "jit_timing.h"
#endif
#if ZU_JIT_EVENT_BLOCKS
#include "jit_event_budget.h"
unsigned zz_jit_event_fallbacks;
#endif
extern unsigned zzuae_engine;
extern "C" unsigned zzuae_jit_validate_current();
#ifdef ZZUAE_JIT_PROFILE
#include "jit_profile.h"
#include "machine.h"
extern "C" void zzuae_jit_profile_finish(){zz_jit_profile.publish(uae_shared+ZJ_PROFILE_BASE);}
#define ZJ_MARK(stage) sample.mark(stage)
#else
#define ZJ_MARK(stage) ((void)0)
#endif
/* Included in newcpu.cpp: retain upstream event/exception/interrupt handling.
 * Count dispatches, not guest instructions, when a dispatch executes a block. */
extern "C" void zzuae_run_accelerated(unsigned limit,uint32_t *dispatches,uint32_t *cycles) {
 const unsigned start=*dispatches;
 while((*dispatches-start)<limit && (!uae_frame_limit || timeframes<uae_frame_limit) && !regs.halted) {
#ifdef ZZUAE_JIT_PROFILE
  ZuJitSample sample(zz_jit_profile);
#endif
  const unsigned before=get_cycles();
  TRY(fault) {
   regs.pissoff=0;
   bool translate=zzuae_engine==1;
#if ZU_JIT_TRACE_INSTRUCTIONS == 1 || ZU_JIT_EVENT_BLOCKS
   // Learned cycle totals are valid only for fixed-cost instructions.
   translate=translate && zzuae_constant_cycles(get_diword(0));
#endif
   ZJ_MARK(ZJ_DISPATCH);
   if(translate) {
    // No linked-block run can hide cancellation from the host indefinitely.
    const unsigned group_cycles=zzuae_jit_validate_current();
    ZJ_MARK(ZJ_VALIDATION);
#if ZU_JIT_TRACE_INSTRUCTIONS == 1 || ZU_JIT_EVENT_BLOCKS
    // Validation and cache reclamation are host work, not guest clock ticks.
    regs.pissoff=0;
#endif
#if ZU_JIT_EVENT_BLOCKS
    if(!zzuae_group_fits(group_cycles,get_cycles(),nextevent,
                         regs.spcflags || uae_int_requested || regs.t0 || regs.t1)) {
     translate=false;++zz_jit_event_fallbacks;
    }
#endif
    ZJ_MARK(ZJ_DISPATCH);
    if(translate){((void(*)())pushall_call_handler)();ZJ_MARK(ZJ_HANDLER);}
   }
   if(!translate) {
    regs.instruction_pc=m68k_getpc();regs.opcode=get_diword(0);
    cpu_cycles=adjust_cycles(cpufunctbl[regs.opcode](regs.opcode));
    do_cycles(cpu_cycles);
    ZJ_MARK(ZJ_INTERPRETER);
   }
#ifdef ZZUAE_JIT_PROFILE
   zz_jit_service_active=sample.active;
#endif
   check_uae_int_request();
   if(regs.spcflags && !regs.halted)do_specialties(0);
   ZJ_MARK(ZJ_EVENTS);
  } CATCH(fault) {bus_error();} ENDTRY
#ifdef ZZUAE_JIT_PROFILE
  zz_jit_service_active=false;
#endif
  *cycles+=(get_cycles()-before)/(CYCLE_UNIT/2);++*dispatches;
  ZJ_MARK(ZJ_DISPATCH);
 }
}
