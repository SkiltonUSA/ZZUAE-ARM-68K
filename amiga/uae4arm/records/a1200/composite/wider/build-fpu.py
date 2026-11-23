from pathlib import Path
import sys,runpy
sys.path.insert(0,'scripts')
import build_uae4arm as b
base=b.OUT/'a1200/build/jit-execution-32768-instruction-timing-movw-events-armv7-flatcycles-earlydraw-pressure-registers-batch-neonplanes-neonhalf-chipreads-pixel4'
b.OUT=b.OUT/'a1200/composite/pixel-fpu'
b.OUT.mkdir(exist_ok=True)
sys.argv=['build_uae4arm_fpu.py','--base',str(base),'--hardware']
runpy.run_path('scripts/build_uae4arm_fpu.py',run_name='__main__')
