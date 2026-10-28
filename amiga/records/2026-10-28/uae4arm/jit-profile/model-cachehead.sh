set -eu
P=.tools/dosbox-model-venv/bin/python
L=.context/amiga/uae4arm/jit-profile
E=.context/amiga/uae4arm/jit-execution-32768-instruction-timing-movw-events-armv7-cachehead/uae-machine.elf
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --cache-head --mmu --expect-bitfields > "$L/guest-cachehead.log" 2>&1
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --cache-head --mmu --cancel > "$L/cancel-cachehead.log" 2>&1
$P tests/amiga/uae4arm/jit_guest.py --cache32 --event-blocks --movw-constants --armv7-emitter --cache-head --mmu --fault > "$L/fault-cachehead.log" 2>&1
$P tests/amiga/uae4arm/jit_timing.py --elf "$E" --cache32 --event-blocks --fixtures beam branch irq pressure groups --output "$L/model-cachehead" > "$L/timing-cachehead.log" 2>&1
