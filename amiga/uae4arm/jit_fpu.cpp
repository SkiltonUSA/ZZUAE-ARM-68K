/* No guest FPU. Generated handlers have already advanced past the opcode.
 * Match upstream fpu_op_illg: report the faulting instruction, not its operands. */
#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "memory.h"
#include "newcpu.h"
static void no_fpu(uae_u32 op){
 regs.fp_exception=true;
 m68k_setpc(regs.instruction_pc);
 op_illg(op);
}
void fpuop_arithmetic(uae_u32 op,uae_u16){no_fpu(op);}
void fpuop_scc(uae_u32 op,uae_u16){no_fpu(op);}
void fpuop_dbcc(uae_u32 op,uae_u16){no_fpu(op);}
void fpuop_trapcc(uae_u32 op,uaecptr,uae_u16){no_fpu(op);}
void fpuop_bcc(uae_u32 op,uaecptr,uae_u32){no_fpu(op);}
void fpuop_save(uae_u32 op){no_fpu(op);}
void fpuop_restore(uae_u32 op){no_fpu(op);}
void jit_abort(const char*,...){
#if ZU_JIT_TRACE_INSTRUCTIONS == 1 || ZU_JIT_EVENT_BLOCKS
 exit((int)(uintptr_t)__builtin_return_address(0));
#else
 abort();
#endif
}
