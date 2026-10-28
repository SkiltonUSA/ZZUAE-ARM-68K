import sys,unittest
from pathlib import Path
root=Path(__file__).absolute().parents[3];sys.path.insert(0,str(root/'scripts'))
from prepare_uae4arm_jit_lists import fast_promotion
class PrepareLists(unittest.TestCase):
 def test_requires_one_pinned_function(self):
  for source in ['', 'void other(){}', 'void raise_in_cl_list(blockinfo* bi)\n{\n'*2]:
   with self.assertRaises(AssertionError):fast_promotion(source)
 def test_preserves_surrounding_code(self):
  marker='void raise_in_cl_list(blockinfo* bi)\n{\n'
  body='  remove_from_cl_list(bi);\n  add_to_cl_list(bi);\n}\n'
  result=fast_promotion('BEFORE\n'+marker+body+'AFTER\n')
  self.assertNotEqual(result,'BEFORE\n'+marker+body+'AFTER\n')
  self.assertTrue(result.startswith('BEFORE\n'+marker))
  self.assertTrue(result.endswith(body+'AFTER\n'))
if __name__=='__main__':unittest.main()
