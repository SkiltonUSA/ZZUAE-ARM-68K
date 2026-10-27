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
/* CPU diagnostic only: exercise translated branches near the end of a large
 * cache without spending minutes filling it. Called immediately after flush. */
extern "C" void zzuae_jit_test_tail(void) {
 current_compile_p=max_compile_start-65536;
#if defined(CPU_arm) && !defined(ARMV6T2) && !defined(CPU_AARCH64)
 reset_data_buffer();
#endif
}
