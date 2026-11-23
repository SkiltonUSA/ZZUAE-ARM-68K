"""Compare real source dispatch blocks, including idle and reserved modes."""
from pathlib import Path
import subprocess

p = Path('.context/amiga/uae4arm/a1200/cycle-costs')
g = p.parent / 'gameplay'
functions = []
for variant, name in [('pixel4', 'reference'), ('fetch-idle-guard', 'candidate')]:
    source = (g / ('build-' + variant) / 'src/custom.cpp').read_text()
    start = source.index('\tif (dma && plf_state != plf_wait_stop)',
                         source.index('STATIC_INLINE int one_fetch_cycle_0'))
    end = source.index('\n\tif (bpl1dat_written)', start)
    functions.append('void ' + name + '(int dma,int fm){\n' + source[start:end] + '}\n')
source = '''#include <cassert>
#include <cstdio>
int plf_state,plf_wait_stop=3,fetch_cycle,fetchstart_mask,fm_maxplane;
int observed,mode_seen,calls;
static const int cycle_sequences[24]={2,1,2,1,2,1,2,1,4,2,3,1,4,2,3,1,8,4,6,2,7,3,5,1};
void fetch(int nr,int fm){observed=nr;mode_seen=fm;++calls;}
''' + '\n'.join(functions) + '''
int main(){unsigned cases=0;
for(int fm=0;fm<3;++fm)for(int planes=0;planes<=16;++planes)
for(int mask: {0,1,3,7,15,31})for(int cycle=0;cycle<256;++cycle)
for(int dma=0;dma<2;++dma)for(int state=0;state<6;++state){
 fm_maxplane=planes;fetchstart_mask=mask;fetch_cycle=cycle;plf_state=state;
 observed=-1;mode_seen=-1;calls=0;reference(dma,fm);
 int plane=observed, mode=mode_seen, count=calls;
 observed=-1;mode_seen=-1;calls=0;candidate(dma,fm);
 assert(observed==plane && mode_seen==mode && calls==count);++cases;
}
printf("PASS %u source dispatch comparisons, including idle/reserved modes\\n",cases);
}
'''
source = '#include <initializer_list>\n' + source
(p / 'fetch-dispatch.cpp').write_text(source)
subprocess.run(['clang++', '-std=c++11', '-O2', '-fsanitize=address,undefined',
                str(p / 'fetch-dispatch.cpp'), '-o', str(p / 'fetch-dispatch')], check=True)
subprocess.run([str(p / 'fetch-dispatch')], check=True)
