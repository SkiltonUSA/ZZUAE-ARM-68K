from pathlib import Path
import subprocess
from transform import change, function

p = Path(__file__).resolve().parent
source = (p.parent/'gameplay/build-pixel4/src/custom.cpp').read_text()
prefix = '''
#include <array>
#include <vector>
#include <cassert>
#include <cstdio>
constexpr int SPR0_HPOS=0x15, MAX_SPRITES=8;
struct Sprite { int dmacycle; };
'''
fixture = '''
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
'''
code = prefix + 'namespace reference {\n'+fixture+function(source)+'}\n'
code += 'namespace candidate {\n'+fixture+function(change(source))+'}\n'
code += '''
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
  printf("PASS %u partial-range comparisons; %u DMA callbacks retain order/state/bounds\\n",checks,slots);
}
'''
code='\n'.join(line.expandtabs(2).rstrip() for line in code.splitlines())+'\n'
(p/'native.cpp').write_text(code)
subprocess.run(['c++','-std=c++17','-O2','-g','-fsanitize=address,undefined',
                '-fno-sanitize-recover=all',str(p/'native.cpp'),'-o',str(p/'native')],check=True)
subprocess.run([str(p/'native')],check=True)
