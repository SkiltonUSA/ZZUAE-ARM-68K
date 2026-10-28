import subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).absolute().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_uae4arm_jit_batch import batch_context
class Batch(unittest.TestCase):
 def test_dispatcher_traces_and_faults(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp);(path/'jit_dispatch_batched.inc').write_text(batch_context((ROOT/'amiga/uae4arm/jit_dispatch.inc').read_text()))
   subprocess.run(['clang++','-std=c++11','-O2','-fsanitize=undefined','-I'+str(path),'-I'+str(ROOT/'amiga/uae4arm'),str(ROOT/'tests/amiga/uae4arm/jit_batch.cpp'),'-o',str(path/'test')],check=True)
   subprocess.run([str(path/'test')],check=True)
if __name__=='__main__':unittest.main()
