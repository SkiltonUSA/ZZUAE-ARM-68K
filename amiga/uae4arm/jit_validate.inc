/* Included after upstream checksum helpers. Older 68000 software can modify
 * RAM code without 68020 cache instructions. Validate the entry block before
 * dispatch; linked-block chaining is disabled by the bounded dispatcher. */
extern "C" void zzuae_jit_validate_current(void) {
 blockinfo *bi=get_blockinfo_addr(regs.pc_p);
 if(bi && bi->csi && bi->status==BI_ACTIVE) {
  bi->status=BI_NEED_CHECK;
  block_check_checksum(bi);
 }
}
