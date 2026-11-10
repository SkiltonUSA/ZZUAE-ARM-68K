def change(source):
    start = source.index('static void do_sprites (int hpos)\n{')
    end = source.index('static void init_sprites', start)
    part = source[start:end]
    begin = part.index('  for (i = minspr; i <= maxspr; i++) {')
    finish = part.index('\n  last_sprite_hpos = hpos;', begin)
    part = part[:begin] + '''  /* Only slots 0 and 2 of each sprite group perform DMA work.
   * Preserve partial catch-up bounds and the original slot order. */
  for (i = minspr + ((minspr - SPR0_HPOS) & 1); i <= maxspr; i += 2) {
    int num = (i - SPR0_HPOS) / 4;
    int cycle = ((i - SPR0_HPOS) >> 1) & 1;
    if (cycle == 0)
      spr[num].dmacycle = 0;
    do_sprites_1 (num, cycle, i);
  }
''' + part[finish:]
    return source[:start] + part + source[end:]


def function(source):
    start = source.index('static void do_sprites (int hpos)\n{')
    return source[start:source.index('static void init_sprites', start)]
