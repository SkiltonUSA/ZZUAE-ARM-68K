    if (zu_sprite_neon_ready && datab && !do_collisions && mask == 0
        && dbl >= 0 && dbl <= 2
        && ((bplcon3 & 2) || (sprxp >= sprite_minx && sprxp + (16 << dbl) <= sprite_maxx))) {
        zu_sprite_or16(buf, datab, 2 * num, dbl);
        ++zu_sprite_neon_spans;
        return;
    }
