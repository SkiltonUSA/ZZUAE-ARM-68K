import subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).absolute().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_uae4arm_disk_activity import disk_activity
class DiskActivity(unittest.TestCase):
 def test_real_fifo_read_path(self):
  source=disk_activity((ROOT/'.context/uae4arm-review/src/disk.cpp').read_text())
  start=source.index('uae_u16 DSKDATR (void)');end=source.index('\nuae_u16 disk_dmal',start)
  fixture='''
#include <cassert>
#include <cstdio>
typedef unsigned short uae_u16;
#define _T(x) x
static unsigned zz_read_words, selected,disabled,dskdmaen,dsklength,pulses;
static int fifo_inuse[3];static uae_u16 fifo[3];
enum {DSKDMA_READ=2,DSKDMA_WRITE=3,LED_DF0=1};
void gui_flicker_led(int led,int unit,int status){assert(led==1&&unit<2&&status==1);++pulses;}
void write_log(const char*){}
int disk_fifostatus(){return 0;}
void disk_dmafinished(){dskdmaen=0;}
'''+source[start:end]+'''
int main(){
 dskdmaen=DSKDMA_READ;selected=2;dsklength=1000;
 for(unsigned n=0;n<600;++n){fifo_inuse[0]=1;fifo[0]=n;assert(DSKDATR()==n);}
 assert(pulses==3);DSKDATR();assert(pulses==3);
 dskdmaen=DSKDMA_WRITE;for(unsigned n=0;n<300;++n){fifo_inuse[0]=2;DSKDATR();}assert(pulses==3);
 dskdmaen=DSKDMA_READ;selected=3;for(unsigned n=0;n<300;++n){fifo_inuse[0]=1;DSKDATR();}assert(pulses==3);
 selected=1;zz_read_words=0;fifo_inuse[0]=1;DSKDATR();assert(pulses==4);
 puts("PASS actual DSKDATR read bursts: DF0/DF1, FIFO data, empty FIFO, write and deselection");
}
'''
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);(p/'test.cpp').write_text(fixture)
   subprocess.run(['clang++','-std=c++11','-fsanitize=address,undefined',str(p/'test.cpp'),'-o',str(p/'test')],check=True)
   subprocess.run([str(p/'test')],check=True)
if __name__=='__main__':unittest.main()
