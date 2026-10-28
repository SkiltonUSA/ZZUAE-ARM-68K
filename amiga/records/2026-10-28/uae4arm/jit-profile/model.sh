set -eu
P=.tools/dosbox-model-venv/bin/python
L=.context/amiga/uae4arm/jit-profile
E=.context/amiga/uae4arm/jit-execution-32768-instruction-timing-movw-events-armv7-profile/uae-machine.elf
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --jit-profile --mmu --expect-bitfields > "$L/guest.log" 2>&1
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --jit-profile --mmu --cancel > "$L/cancel.log" 2>&1
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --jit-profile --mmu --fault > "$L/fault.log" 2>&1
$P tests/amiga/uae4arm/jit_timing.py --elf "$E" --cache32 --event-blocks --jit-profile --fixtures beam branch irq pressure groups --output "$L/model" > "$L/timing.log" 2>&1
