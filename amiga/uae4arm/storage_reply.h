#pragma once
#include "storage_wire.h"
#include "../arm_debug/protocol.h"

static inline void us_publish_reply(volatile uint8_t *shared,
                                    const struct ad_io *io,
                                    uint32_t sequence, uint32_t result) {
    /* A combined cache flush can expose the lower-address reply first.
     * Make the result visible before publishing completion to ARM. */
    ad_put(shared, US_RESULT, result);
    io->push(shared + US_RESULT, 4, io->user);
    io->barrier(io->user);
    ad_put(shared, US_REPLY, sequence);
    io->push(shared + US_REPLY, 4, io->user);
    io->barrier(io->user);
}
