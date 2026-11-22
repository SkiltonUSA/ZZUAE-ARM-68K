# ZZOverclock in Settings

The launcher offers **666.7 MHz (standard)** and **800 MHz (experimental)**.
Refresh reads the current board clock; Apply changes it after checking the
firmware, ARM activity, temperature and clock ownership. Close ARM applications
before applying a change. This setting affects the whole ZZ9000.

Overclocking is optional. Normal launch at the standard clock does not require
the custom clock service. If the service is absent or unavailable, clock control
stays disabled. Opening the launcher, changing models and saving settings never
change the clock. There is no automatic firmware installation or startup change.

The bundled `ZZClock` client must stay beside the launcher. ZZNintendo keeps one
beside each model's Frontend. Clock control requires the experimental ABI 3
firmware; standard XACP alone is insufficient. The standalone ZZOverclock app
and the embedded controls use the same service and session identity.

800 MHz requires clock-aware emulator builds and suitable cooling. The 60 C
preflight check is not a continuous thermal watchdog. Existing 800 MHz sessions
are preserved until an explicit successful clock change or reset.

Implementation: `amiga/common/zzclock/`. The client takes the shared ARM exclusion
port even for STATUS, preventing it from touching the XACP mailbox during a
running emulator. It uses the firmware service; the launcher writes no PLL
registers and performs no Core0/Core1 work itself.
