import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).absolute().parents[3]/'scripts'))
from prepare_uae4arm_jit_service import service_profile

class ServiceTransform(unittest.TestCase):
 def test_scopes_only_inside_specialties(self):
  source='''void elsewhere(){do_copper ();}
static int do_specialties (int cycles){
  do_copper ();
  while ((regs.spcflags & SPCFLAG_STOP) && !cancel){do_copper ();}
  if (regs.spcflags & SPCFLAG_TRACE)trace();
  return 0;
}
/* It's really sad */
void later(){do_copper ();}
'''
  out=service_profile(source,'#include "profile.h"')
  self.assertIn('void elsewhere(){do_copper ();}',out)
  self.assertTrue(out.endswith('void later(){do_copper ();}\n'))
  self.assertIn('#include "profile.h"\nstatic int do_specialties',out)
  self.assertEqual(out.count('ZuJitInterval copper('),2)
  self.assertEqual(out.count('copper.finish();'),2)
  self.assertEqual(out.count('ZuJitInterval stop('),1)
  self.assertIn('zz_jit_service_active && (regs.spcflags & SPCFLAG_STOP)',out)
  self.assertIn('  stop.finish(); }\n  if (regs.spcflags & SPCFLAG_TRACE)',out)
 def test_missing_stop_boundary_rejected(self):
  for body in ('', '  while ((regs.spcflags & SPCFLAG_STOP)){}',
               '  if (regs.spcflags & SPCFLAG_TRACE){}'):
   with self.subTest(body=body),self.assertRaises(AssertionError):
    service_profile("static int do_specialties (int cycles){"+body+"} /* It's really sad */",'')
if __name__=='__main__':unittest.main()
