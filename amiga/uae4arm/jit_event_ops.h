#pragma once
/* This whitelist excludes memory, control flow, SR changes and exceptions.
 * Operand modes alone are insufficient: e.g. STOP and RESET have no RAM EA. */
static bool zzuae_register_op(unsigned opcode) {
 const instr &op=table68k[opcode];
 if(!zzuae_constant_cycles(opcode))return false;
 if(op.suse && op.smode!=Dreg && op.smode!=Areg &&
    (op.smode<imm || op.smode>immi))return false;
 if(op.duse && op.dmode!=Dreg && op.dmode!=Areg)return false;
 switch(op.mnemo) {
#ifdef ZU_JIT_MORE_REGISTERS
 case i_BTST:case i_BCHG:case i_BCLR:case i_BSET:case i_Scc:
 case i_ASR:case i_ASL:case i_LSR:case i_LSL:
 case i_ROL:case i_ROR:case i_ROXL:case i_ROXR:return true;
#endif
 case i_MOVE:case i_MOVEA:case i_ADD:case i_ADDA:case i_ADDX:
 case i_SUB:case i_SUBA:case i_SUBX:case i_AND:case i_OR:case i_EOR:
 case i_CMP:case i_CMPA:case i_CLR:case i_NOT:case i_NEG:case i_NEGX:
 case i_TST:case i_SWAP:case i_EXG:case i_EXT:case i_NOP:return true;
 default:return false;
 }
}
