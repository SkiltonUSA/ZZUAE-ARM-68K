# Event-bounded JIT / A9 emitter evidence

See [the report](../../../../../docs/amiga-uae4arm-jit-events.md) for methods,
results and limits. Workspace paths are normalised to `<workspace>` and the
installation drawer to `ZZUAE:`. No ROMs or disk images are included.

## Builds

- `a1/a2`: instruction-sized MOVW/MOVT timing reference, player CRC `5F193670`.
- `b1/b2`: register-only event groups, duplicate metadata lookup, player CRC
  `AA945FFE`; source commit `78f4f01`.
- `c1/c2`: event groups with one lookup, player CRC `008C1734`; source commit
  `300f529`.
- `d1/d2`: event groups plus upstream ARMv6T2 A32 emitter, player CRC `6617242E`;
  source commit `96f1fc8`.
- `i1`: matching 68020 interpreter control in the `d` payload.

All JIT variants use a 32 MiB code cache and 64 MiB runtime allocation.
`builds-*.json` preserves tested binary hashes. The CPU fixture was expanded from
432 to 528 cases after the initial one-lookup hardware build; the corresponding
logs are labelled `expanded`/`counts`. Only the diagnostic fixture changed in
that expansion. `compile-armv7.json` records the candidate flags/upstream pin.

## Records

- `hardware/`: physical results, including the failed long audio runs.
- `measurements.json`: individual headless timings, final-state checks and means.
- `final-model/`, `lookup-model/`, `armv7-model/`: interpreter/JIT timing states.
- `guest-*.log`: translated CPU comparisons, including code-cache-tail checks.
- `cancel-*.log`, `fault-*.log`: instruction-model cleanup checks.
- `bitfields.log`: execution of upstream BFI/BFC/UBFX encodings.
- `*-red.log`: selected expected pre-fix/pre-feature failures.
- `native-export.log`: exported C++ helper tests compiled with UBSan and run.
- `quality.log`: UB tools report unsupported C++ inputs; not a coverage claim.
- `SHA256.json`: hashes of the curated evidence files.

Live delivery is asynchronous; displayed-frame counts and queue-gap observations
are recorded, not treated as deterministic guest-state checks. Nonzero PCM and
AHI completion do not establish audible quality. The release and installed
application were not replaced by these experiments.
