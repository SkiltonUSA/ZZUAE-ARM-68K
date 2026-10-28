"""Avoid relinking an entry already at the front of its JIT cache bucket."""

def fast_promotion(source):
    marker = 'void raise_in_cl_list(blockinfo* bi)\n{\n'
    assert source.count(marker) == 1, 'upstream cache promotion changed'
    return source.replace(marker, marker + '''  uae_u32 cl = cacheline(bi->pc_p);
  if (cache_tags[cl+1].bi == bi) {
    // Handler selection may have changed during checksum invalidation.
    cache_tags[cl].handler = bi->handler_to_use;
    return;
  }
''', 1)
