
#include <array>
#include <vector>
#include <cassert>
#include <cstdio>
constexpr int SPR0_HPOS=0x15, MAX_SPRITES=8;
struct Sprite { int dmacycle; };
namespace reference {

int vpos, sprite_vblank_endline=25, last_sprite_hpos;
Sprite spr[8];
std::vector<std::array<int,11>> events;
void do_sprites_1(int num,int cycle,int hpos) {
  std::array<int,11> event{num,cycle,hpos};
  for(int n=0;n<8;++n)event[n+3]=spr[n].dmacycle;
  events.push_back(event);
  // A callback changes state which the paired sprite can observe later.
  spr[num].dmacycle=(cycle==0);
}
static void do_sprites (int hpos)
{
  int maxspr, minspr;
  int i;

  if (vpos < sprite_vblank_endline)
    return;

  maxspr = hpos;
  minspr = last_sprite_hpos + 1;

  if (minspr >= maxspr || last_sprite_hpos == hpos)
    return;

  if (maxspr >= SPR0_HPOS + MAX_SPRITES * 4)
    maxspr = SPR0_HPOS + MAX_SPRITES * 4 - 1;
  if (minspr < SPR0_HPOS)
    minspr = SPR0_HPOS;

  if (minspr == maxspr)
    return;

  for (i = minspr; i <= maxspr; i++) {
    int cycle = -1;
    int num = (i - SPR0_HPOS) / 4;
    switch ((i - SPR0_HPOS) & 3)
    {
      case 0:
        cycle = 0;
        spr[num].dmacycle = 0;
        break;
      case 2:
        cycle = 1;
        break;
    }
    if (cycle >= 0) {
      do_sprites_1 (num, cycle, i);
    }
  }

  last_sprite_hpos = hpos;
}

}
namespace candidate {

int vpos, sprite_vblank_endline=25, last_sprite_hpos;
Sprite spr[8];
std::vector<std::array<int,11>> events;
void do_sprites_1(int num,int cycle,int hpos) {
  std::array<int,11> event{num,cycle,hpos};
  for(int n=0;n<8;++n)event[n+3]=spr[n].dmacycle;
  events.push_back(event);
  // A callback changes state which the paired sprite can observe later.
  spr[num].dmacycle=(cycle==0);
}
static void do_sprites (int hpos)
{
  int maxspr, minspr;
  int i;

  if (vpos < sprite_vblank_endline)
    return;

  maxspr = hpos;
  minspr = last_sprite_hpos + 1;

  if (minspr >= maxspr || last_sprite_hpos == hpos)
    return;

  if (maxspr >= SPR0_HPOS + MAX_SPRITES * 4)
    maxspr = SPR0_HPOS + MAX_SPRITES * 4 - 1;
  if (minspr < SPR0_HPOS)
    minspr = SPR0_HPOS;

  if (minspr == maxspr)
    return;

  /* Only slots 0 and 2 of each sprite group perform DMA work.
   * Preserve partial catch-up bounds and the original slot order. */
  for (i = minspr + ((minspr - SPR0_HPOS) & 1); i <= maxspr; i += 2) {
    int num = (i - SPR0_HPOS) / 4;
    int cycle = ((i - SPR0_HPOS) >> 1) & 1;
    if (cycle == 0)
      spr[num].dmacycle = 0;
    do_sprites_1 (num, cycle, i);
  }

  last_sprite_hpos = hpos;
}

}

int main() {
  unsigned checks=0, slots=0;
  for(int v:{24,25,26})for(int last=-4;last<=300;++last)
  for(int now=-4;now<=300;++now)for(int mask:{0,0x55,0xaa,0xff}) {
    reference::vpos=candidate::vpos=v;
    reference::last_sprite_hpos=candidate::last_sprite_hpos=last;
    reference::events.clear();candidate::events.clear();
    for(int n=0;n<8;++n)
      reference::spr[n].dmacycle=candidate::spr[n].dmacycle=(mask>>n)&1;
    reference::do_sprites(now);candidate::do_sprites(now);
    assert(reference::events==candidate::events);
    assert(reference::last_sprite_hpos==candidate::last_sprite_hpos);
    for(int n=0;n<8;++n)assert(reference::spr[n].dmacycle==candidate::spr[n].dmacycle);
    slots+=reference::events.size();++checks;
  }
  printf("PASS %u partial-range comparisons; %u DMA callbacks retain order/state/bounds\n",checks,slots);
}
