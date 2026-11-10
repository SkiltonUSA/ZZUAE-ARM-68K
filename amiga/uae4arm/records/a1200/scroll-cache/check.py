from pathlib import Path
import subprocess,sys
p=Path(__file__).resolve().parent
s=(p.parent/'gameplay/build-pixel4/src/custom.cpp').read_text()
a=s.index('STATIC_INLINE void compute_toscr_delay_1 (int bplcon1)');z=s.index('STATIC_INLINE void compute_toscr_delay (',a)
f=s[a:z];x=f.index('{')+1;y=f.rindex('}')
entry=(p/'entry.inc').read_text()
if '--broken' in sys.argv:entry=entry.replace(' && plan.res == toscr_res','')
c=f[:x]+'\n'+entry+f[x:y]+(p/'exit.inc').read_text()+f[y:]
header='#define STATIC_INLINE static inline\n#define HARD_DDF_START_REAL 0x18\n#define RES_MAX 2\nint fetchmode_mask,fetchmode_size,fetchstart_mask,bpl_hstart,toscr_res,toscr_delay[2];\n'
source='#include <cassert>\n#include <cstdio>\n#include <random>\n'+header+f.replace('compute_toscr_delay_1','reference')+c+r"""
unsigned tests;
void check(int con) {
 reference(con); int a=toscr_delay[0],b=toscr_delay[1];
 for(int repeat=0;repeat<3;repeat++){
  toscr_delay[0]=toscr_delay[1]=-1;
  compute_toscr_delay_1(con);
  assert(toscr_delay[0]==a && toscr_delay[1]==b);tests++;
 }
}
int main(){
 std::mt19937 rng(1200);
 for(unsigned n=0;n<100000;n++){
  int con=n<65536?n:rng()&65535;
  fetchmode_size=16<<(rng()%3); fetchmode_mask=fetchmode_size-1;
  fetchstart_mask=(1<<(1+rng()%5))-1; bpl_hstart=int(rng()%300)-20;
  for(int r=0;r<3;r++){
   toscr_res=r;check(con);check(con^0x1234);check(con);
   int* fields[]={&fetchmode_mask,&fetchmode_size,&fetchstart_mask,&bpl_hstart,&toscr_res};
   int values[]={fetchmode_mask^16,fetchmode_size^32,fetchstart_mask^8,bpl_hstart+1,(r+1)%3};
   for(int i=0;i<5;i++){int old=*fields[i];*fields[i]=values[i];check(con);*fields[i]=old;check(con);}
  }
 }
 printf("PASS %u exact comparisons: all BPLCON1 values, repeated calls, each dependency mutated alone\n",tests);
}
"""
(p/'native.cpp').write_text('\n'.join(line.rstrip() for line in source.splitlines())+'\n')
subprocess.run(['clang++','-O2','-fsanitize=address,undefined',str(p/'native.cpp'),'-o',str(p/'native')],check=True)
subprocess.run([str(p/'native')],check=True)
