"""Bound the experimental 32 MiB A32 cache and reject wrapped branches."""
def cache_limits(source, kib):
    if kib != 32768:
        return source
    old = 'compiled_code + cache_size*1024 - BYTES_PER_INST'
    assert source.count(old) == 2
    return source.replace(old, 'compiled_code + cache_size*1024 - POPALLSPACE_SIZE - 8 - BYTES_PER_INST')


def checked_branches(source, kib):
    if kib != 32768:
        return source
    old = '''\tuintptr off = ((uintptr)a - (uintptr)jmpaddr - 8) >> 2;
\t*(jmpaddr) = (*(jmpaddr) & 0xff000000) | (off & 0x00ffffff);'''
    assert old in source
    return '#include "jit_branch.inc"\n' + source.replace(old, '''  uint32_t instruction;
  if(!zj_branch(*jmpaddr,(uintptr)jmpaddr,a,&instruction))abort();
  *jmpaddr=instruction;''')
