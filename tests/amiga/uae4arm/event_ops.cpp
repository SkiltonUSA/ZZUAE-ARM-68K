#include <cassert>
#include <initializer_list>
#define ENUMDECL typedef enum
#define ENUMNAME(name) name
#include "readcpu.h"
static instr entry;
instr *table68k=&entry;
static bool fixed=true;
static bool zzuae_constant_cycles(unsigned){return fixed;}
#include "jit_event_ops.h"
int main(){
 entry.mnemo=i_ADD;entry.suse=entry.duse=1;entry.smode=imm;entry.dmode=Dreg;
 assert(zzuae_register_op(0));
 fixed=false;assert(!zzuae_register_op(0));fixed=true;
 entry.smode=Aind;assert(!zzuae_register_op(0));
 entry.smode=PC16;assert(!zzuae_register_op(0));
 entry.smode=Dreg;entry.dmode=Aipi;assert(!zzuae_register_op(0));
 entry.dmode=Areg;assert(zzuae_register_op(0));
 entry.suse=entry.duse=0;
 for(unsigned op:{i_STOP,i_RESET,i_RTE,i_RTS,i_MV2SR,i_Bcc,i_DBcc,i_DIVU,i_TRAP,i_ILLG}){
  entry.mnemo=op;assert(!zzuae_register_op(0));
 }
 entry.mnemo=i_NOP;assert(zzuae_register_op(0));
}
