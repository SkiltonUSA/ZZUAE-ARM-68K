"""Optional Chip RAM read fast path for the 68020 interpreter only."""


def chip_reads(tree):
    header = tree / 'include/memory.h'
    source = header.read_text()
    for width, callback, value in (
        ('long', 'lget', 'do_get_mem_long((uae_u32*)(bank->baseaddr+(addr&bank->mask)))'),
        ('word', 'wget', 'do_get_mem_word((uae_u16*)(bank->baseaddr+(addr&bank->mask)))'),
        ('byte', 'bget', 'bank->baseaddr[addr&bank->mask]'),
    ):
        original = f'STATIC_INLINE uae_u32 get_{width}(uaecptr addr)\n{{\n  return {width}get(addr);\n}}'
        replacement = f'''STATIC_INLINE uae_u32 get_{width}(uaecptr addr)
{{
#ifdef ZZUAE_CPU_CHIP_READS
  /* The pinned chipmem read callbacks only mask the address and read RAM.
   * ROM, custom registers and every other bank retain their callbacks.
   * Writes retain the existing invalidation and device semantics. */
  addrbank *bank=&get_mem_bank(addr);
  if(bank==&chipmem_bank)return {value};
  return bank->{callback}(addr);
#else
  return {width}get(addr);
#endif
}}'''
        assert source.count(original) == 1, width
        source = source.replace(original, replacement)
    header.write_text(source)
    # Do not alter chipset DMA, the compatible interpreter or JIT helpers.
    cpu = tree / 'cpuemu_0.cpp'
    cpu.write_text('#define ZZUAE_CPU_CHIP_READS 1\n' + cpu.read_text())
