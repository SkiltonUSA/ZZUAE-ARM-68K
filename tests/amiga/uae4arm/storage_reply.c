#include "storage_reply.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Model a 68060 cache-line writeback that exposes the reply word first.
 * The ARM consumer checks the result as soon as it sees the new sequence. */
static uint32_t cache_words[(US_CONTROL + 128) / 4];
static uint32_t ram_words[(US_CONTROL + 128) / 4];
static uint32_t expected_sequence, expected_result, observed;
static void push(volatile void *p, size_t n, void *user) {
    (void)user;
    volatile uint8_t *cache = (volatile uint8_t *)cache_words;
    volatile uint8_t *ram = (volatile uint8_t *)ram_words;
    size_t first = ((volatile uint8_t *)p - cache) & ~(size_t)15;
    size_t end = (((volatile uint8_t *)p - cache) + n + 15) & ~(size_t)15;
    for (size_t at = first; at < end; at += 4) {
        ad_put(ram, at, ad_get(cache, at));
        if (!observed && ad_get(ram, US_REPLY) == expected_sequence) {
            assert(ad_get(ram, US_RESULT) == expected_result);
            observed = 1;
        }
    }
}
static void barrier(void *user) { (void)user; }
int main(void) {
    const struct ad_io io = {0, push, barrier, 0, 0};
    const uint32_t sizes[] = {512, 3072, 16384, 512, 0};
    for (unsigned i = 0; i < sizeof sizes / sizeof sizes[0]; ++i) {
        expected_sequence = i + 1;
        expected_result = sizes[i];
        observed = 0;
        us_publish_reply((volatile uint8_t *)cache_words, &io,
                         expected_sequence, expected_result);
        assert(observed);
    }
    puts("PASS storage completion publishes changed lengths and failures before ACK");
    return 0;
}
