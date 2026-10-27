# Experimental JIT player evidence

Selected model/native test outputs and physical player logs. The negative
byte-fixture file is an excerpt; full local driver traces remain in the workspace.

- Early `jit-alien1800` is a failed guest run; do not count it as a pass.
- `jit-bytefix-alien1800` and its matching interpreter pass after the correction.
- `headless-*` omit live window presentation; they still run the chipset/renderer.
- `jit-audio-cancel` is a silent-intro lifecycle test.
- Both `*audio6000` runs contain nonzero PCM. Frequent late queue observations
  and differing final game state remain unresolved; these are not audio or
  full-game equivalence passes.
- A screenshot interrupted the Mac driver's polling of `jit-a600-wb20`; the
  completed log was retrieved separately. It is excluded from performance tables.
- `artifact.json` identifies the tested player, CRC C521616C.

See [the report](../../../../../docs/amiga-uae4arm-jit-player.md).
