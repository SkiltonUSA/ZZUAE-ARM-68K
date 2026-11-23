from pathlib import Path
import sys
p=Path('.context/amiga/uae4arm/a1200');base=p/'build/jit-execution-32768-instruction-timing-movw-events-armv7-flatcycles-earlydraw-pressure-registers-batch-neonplanes-neonhalf-chipreads-pixel4'
s=(p/'gameplay/check-candidate.py').read_text().replace("p=Path(__file__).resolve().parent", "p=Path('.context/amiga/uae4arm/a1200/gameplay')").replace("candidate=p/('build-'+variant)/'uae-machine.elf'", "candidate=Path("+repr(str(base/'uae-machine.elf'))+")")
sys.argv=['check-integrated.py','pixel-integrated'];exec(compile(s,'check-integrated.py','exec'))
