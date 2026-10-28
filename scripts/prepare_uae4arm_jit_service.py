"""Instrument explicit Copper service and STOP without changing their cadence."""

def service_profile(cpu, include):
    first = cpu.index('static int do_specialties (int cycles)')
    last = cpu.index("/* It's really sad", first)
    service = cpu[first:last].replace(
        'do_copper ();',
        '{ ZuJitInterval copper(zz_jit_profile,zz_jit_service_active,ZJ_COPPER); do_copper (); copper.finish(); }')
    start = '  while ((regs.spcflags & SPCFLAG_STOP)'
    finish = '  if (regs.spcflags & SPCFLAG_TRACE)'
    assert service.count(start) == 1 and service.count(finish) == 1
    service = service.replace(start,
        '  { ZuJitInterval stop(zz_jit_profile,zz_jit_service_active && (regs.spcflags & SPCFLAG_STOP),ZJ_STOP);\n' + start)
    service = service.replace(finish, '  stop.finish(); }\n' + finish)
    return cpu[:first] + include + '\n' + service + cpu[last:]
