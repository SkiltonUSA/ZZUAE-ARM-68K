# JIT service and scheduling evidence

See [the report](../../../../../docs/amiga-uae4arm-jit-service.md).

- `hardware/`: final profiler, unprofiled comparisons, live audio and long-run logs. The 6,000-frame live timeout and truncated Frontier reference are retained as failed completion gates, despite clean teardown.
- `builds/`: compiler/source/artifact manifests for measured variants. These distinguish binaries sharing version 0.5.4-dev.
- `model/`: interpreter/JIT endpoint comparisons. `all-bits-*` adds nonzero shift counts and all eight register shift/rotate families to the earlier bit fixture.
- `tests/`: CPU suites, cancellation/fault checks, expected failing tests and scoped UB-tool results. Python mutation/coverage figures do not cover C++ or physical cache behaviour.
- `early-audio.json` / `pressure-audio.json`: equal final CPU, RAM, pixels and PCM despite different drawing/presentation counts.
- `profile.json`: final sampled timing counters. Only the first five intervals are exclusive; STOP/Copper are inclusive subintervals.
- `work-log.md`: decisions and validation sequence.

Timings are individual fresh-process measurements, not confidence intervals or gameplay FPS. No listening-quality claim is made. Private media and raw MCP/window-title records are excluded. Paths are redacted; runtime hardware addresses remain observations, never allocation constants.
