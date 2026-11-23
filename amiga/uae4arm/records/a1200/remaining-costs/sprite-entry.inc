    if (!do_collisions && !mask && dbl >= 0 && dbl <= 2 &&
        ((bplcon3 & 2) || (sprxp >= sprite_minx && sprxp + (16 << dbl) <= sprite_maxx))) {
        switch (dbl) {
        case 0: zz_sprite_plain<0>(buf, datab, num); break;
        case 1: zz_sprite_plain<1>(buf, datab, num); break;
        case 2: zz_sprite_plain<2>(buf, datab, num); break;
        }
        return;
    }
