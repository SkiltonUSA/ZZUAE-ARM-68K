/* Experimental A9 emitter. r0=guest address, r1=write data, r12=current
 * UAE bank. The caller has already applied the normal callback ABI spill.
 * Only exact Chip/Slow RAM banks qualify; devices and ROM retain callbacks.
 * No guest address is treated as a native pointer or fixed DDR allocation. */
static uae_u32 *zz_direct_memory(unsigned offset)
{
  if(offset >= 6 * SIZEOF_VOID_P)return NULL; /* PC translation is unchanged. */
  const unsigned slot=offset/SIZEOF_VOID_P;
  const bool write=slot>=3;
  const unsigned size=4u>>(slot%3);
  uae_u32 *slow[3];unsigned n=0;
  LOAD_U32(REG_WORK1,(uintptr)&chipmem_bank);
  CMP_rr(REG_WORK3,REG_WORK1);
  uae_u32 *chip=(uae_u32*)get_target();BEQ_i(0);
  LOAD_U32(REG_WORK1,(uintptr)&bogomem_bank);
  CMP_rr(REG_WORK3,REG_WORK1);
  slow[n++]=(uae_u32*)get_target();BNE_i(0);
  write_jmp_target(chip,(uintptr)get_target());
  if(size>1){
    TST_ri(REG_PAR1,size-1);
    slow[n++]=(uae_u32*)get_target();BNE_i(0);
  }
  LDR_rRI(REG_WORK1,REG_WORK3,offsetof(addrbank,start));
  SUB_rrr(REG_WORK2,REG_PAR1,REG_WORK1);
  LDR_rRI(REG_WORK1,REG_WORK3,offsetof(addrbank,mask));
  AND_rrr(REG_WORK2,REG_WORK2,REG_WORK1);
  ADD_rri(REG_WORK1,REG_WORK2,size);
  LDR_rRI(REG_WORK2,REG_WORK3,offsetof(addrbank,allocated_size));
  CMP_rr(REG_WORK1,REG_WORK2);
  slow[n++]=(uae_u32*)get_target();BHI_i(0);
  SUB_rri(REG_WORK2,REG_WORK1,size);
  LDR_rRI(REG_WORK1,REG_WORK3,offsetof(addrbank,baseaddr));
  if(write){
    if(size==1){STRB_rRR(REG_PAR2,REG_WORK1,REG_WORK2);}
    else if(size==2){REV16_rr(REG_WORK3,REG_PAR2);STRH_rRR(REG_WORK3,REG_WORK1,REG_WORK2);}
    else {REV_rr(REG_WORK3,REG_PAR2);STR_rRR(REG_WORK3,REG_WORK1,REG_WORK2);}
  }else{
    if(size==1){LDRB_rRR(REG_RESULT,REG_WORK1,REG_WORK2);}
    else if(size==2){LDRH_rRR(REG_RESULT,REG_WORK1,REG_WORK2);REV16_rr(REG_RESULT,REG_RESULT);}
    else {LDR_rRR(REG_RESULT,REG_WORK1,REG_WORK2);REV_rr(REG_RESULT,REG_RESULT);}
  }
  uae_u32 *done=(uae_u32*)get_target();B_i(0);
  for(unsigned i=0;i<n;i++)write_jmp_target(slow[i],(uintptr)get_target());
  return done;
}
