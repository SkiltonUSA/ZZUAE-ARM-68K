from pathlib import Path
import sys
script=Path('tests/amiga/uae4arm/check_machine.py').resolve()
base=Path('.context/amiga/uae4arm/a1200/composite/pixel-fpu/fpu-execution').resolve()
s=script.read_text().replace("(out/'fpu-execution/fpu_guest.bin')", "Path("+repr(str(base/'fpu_guest.bin'))+")")
sys.argv=[str(script),'3','--elf',str(base/'uae-machine.elf'),'--cache32','--engine','2','--profile','4','--fpu-fixture','--synthetic-rom','--neon']+sys.argv[1:]
exec(compile(s,str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
