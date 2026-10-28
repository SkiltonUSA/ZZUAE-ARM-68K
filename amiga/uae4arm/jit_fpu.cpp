/* No guest FPU. The opcode table rejects F-line opcodes; these linkage entries
 * must also report the architectural illegal-instruction path if reached. */
#include "sysconfig.h"
#include "sysdeps.h"
#include "options.h"
#include "memory.h"
#include "newcpu.h"
void fpuop_arithmetic(uae_u32 op,uae_u16){op_illg(op);}
void fpuop_scc(uae_u32 op,uae_u16){op_illg(op);}
void fpuop_dbcc(uae_u32 op,uae_u16){op_illg(op);}
void fpuop_trapcc(uae_u32 op,uaecptr,uae_u16){op_illg(op);}
void fpuop_bcc(uae_u32 op,uaecptr,uae_u32){op_illg(op);}
void fpuop_save(uae_u32 op){op_illg(op);}
void fpuop_restore(uae_u32 op){op_illg(op);}
void jit_abort(const char*,...){
#if ZU_JIT_TRACE_INSTRUCTIONS == 1 || ZU_JIT_EVENT_BLOCKS
 exit((int)(uintptr_t)__builtin_return_address(0));
#else
 abort();
#endif
}
