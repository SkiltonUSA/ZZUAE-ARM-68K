set -eu
P=.tools/dosbox-model-venv/bin/python
L=.context/amiga/uae4arm/jit-profile
E=.context/amiga/uae4arm/jit-execution-32768-instruction-timing-movw-events-armv7-flatcycles/uae-machine.elf
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --flat-cycles --mmu --expect-bitfields > "$L/guest-flatcycles.log" 2>&1
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --flat-cycles --mmu --cancel > "$L/cancel-flatcycles.log" 2>&1
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --flat-cycles --mmu --fault > "$L/fault-flatcycles.log" 2>&1
$P tests/amiga/uae4arm/jit_timing.py --elf "$E" --cache32 --event-blocks --fixtures beam branch irq pressure groups --output "$L/model-flatcycles" > "$L/timing-flatcycles.log" 2>&1
