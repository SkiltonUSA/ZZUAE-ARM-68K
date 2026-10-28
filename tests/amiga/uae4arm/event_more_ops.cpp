#include <cassert>
#include <initializer_list>
#define ENUMDECL typedef enum
#define ENUMNAME(name) name
#include "readcpu.h"
static instr entry;
instr *table68k=&entry;
static bool fixed=true;
static bool zzuae_constant_cycles(unsigned){return fixed;}
#define ZU_JIT_MORE_REGISTERS 1
#include "jit_event_ops.h"
int main(){
 for(unsigned op:{i_BTST,i_BCHG,i_BCLR,i_BSET,i_Scc,i_ASR,i_ASL,i_LSR,i_LSL,i_ROL,i_ROR,i_ROXL,i_ROXR}){
  entry.mnemo=op;entry.suse=entry.duse=1;entry.smode=Dreg;entry.dmode=Dreg;
  assert(zzuae_register_op(0));
  fixed=false;assert(!zzuae_register_op(0));fixed=true;
  entry.smode=Aind;assert(!zzuae_register_op(0));entry.smode=Dreg;
  entry.dmode=Aind;assert(!zzuae_register_op(0));
 }
 entry.suse=entry.duse=0;
 for(unsigned op:{i_STOP,i_RESET,i_RTE,i_RTS,i_MV2SR,i_Bcc,i_DBcc,i_DIVU,i_TRAP,i_ILLG}){
  entry.mnemo=op;assert(!zzuae_register_op(0));
 }
}
