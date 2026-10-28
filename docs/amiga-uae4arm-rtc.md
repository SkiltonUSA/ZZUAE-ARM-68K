# Emulated real-time clock

**RTC: On / Off** is available in the launcher. On initialises the guest clock
from the host AmigaOS date and time at launch. The clock advances with the
Cortex-A9 monotonic timer, independently of guest speed and frame rate. It does
not change the host clock. New launcher sessions default to On; the command-line
player stays Off unless passed `RTC ON`.

A1000/A500 profiles expose the upstream MSM6242B-compatible clock; A500 Plus/A600
use RF5C01A-compatible registers. The clock bank is mapped at `$DC0000` only
when enabled. `SetClock LOAD` in a guest startup sequence can read it. This is
an emulated expansion on machines that originally lacked a battery clock.

AmigaOS wall-clock fields have no timezone offset attached, so the displayed
local date/time is carried across directly. The host date must be correct.
There is no persistent emulated battery or saved guest clock adjustment;
`SetClock SAVE` does not set the host clock or persist a new time across launches.

Native calendar tests cover epoch conversion, leap years, the 2038 boundary and
the non-leap year 2100. ARM execution tests read actual mapped clock registers,
check both chip layouts and advance the mocked monotonic timer. Hardware checks
use a private Workbench disk with `SetClock LOAD`, followed by two `Date` commands.
Test disk images and ROMs are not distributed.

The A600 test caught its broad Gayle stub replacing the clock mapping. Mapping
the enabled RTC after Gayle fixes that overlap while retaining the empty IDE and
PCMCIA behaviour. The first timer-advance test wrote directly to a mocked MMIO
register, which the model's read hook immediately replaced; advancing the mock
clock itself corrected the test. Both findings are retained in the test log.

Physical A500/Workbench 1.3 check: `SetClock LOAD` succeeded, then guest `Date`
showed the host's 11 October 2025 clock and advanced from 12:09:19 to 12:09:23
across a guest two-second wait. The difference reflects slower guest execution,
while the RTC follows real elapsed time. No host date correction was made.
The 1,800-frame run completed with both disks inserted, matching DF1 CRC and
clean state/memory restoration.
