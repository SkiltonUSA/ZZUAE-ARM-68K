/* Use the existing word view only when the byte offset is aligned. */
        if ((word_offs & 3) == 0) {
            uae_u32 *words = spixstate.words + word_offs / 4;
            uae_u32 packed = (uae_u32)state * 0x01010101u;
            for (i = 0; i < width; i += 8) {
                words[0] |= packed;
                words[1] |= packed;
                words += 2;
            }
        } else {
ORIGINAL
        }
