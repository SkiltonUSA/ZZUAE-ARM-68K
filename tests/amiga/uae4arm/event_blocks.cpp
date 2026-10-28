#include <cassert>
#include <cstdint>
#include "jit_event_budget.h"
int main() {
 assert(zzuae_group_fits(0, 100, 100));
 assert(!zzuae_group_fits(128, 100, 356, true));
 assert(zzuae_group_fits(0, 100, 356, true));
 assert(zzuae_group_fits(256, 100, 356));
 assert(!zzuae_group_fits(257, 100, 356));
 assert(!zzuae_group_fits(1, 100, 100));
 assert(zzuae_group_fits(256, 0xffffff80u, 0x80));
 assert(!zzuae_group_fits(257, 0xffffff80u, 0x80));
}
