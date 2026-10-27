# UB audit work log

- Scope: the ZZUAE JIT integration, launcher settings and their build/test code from commit 3c43306. Read UB-mode and companion documentation.
- Reviewed execution lifetime, error paths, checksum validation, CPU selection/persistence and build adapters. No broad refactor or unrelated emulator edits.
- Found fatal-error boundary ending before compiler cleanup, plus active-guard leaks on early returns. Add actual ARM model fault/early-return tests before fixing.
- Companion tools support Python, not C/C++/ARM. Their metrics cannot establish emulator coverage or a CRAP score for the runtime.
- Confirmed stale guards on invalid options and rejected diagnostic vector setup. The first success/cleanup test harness lacked the machine timer mapping and synthetic boot setup; corrected it against the existing model harness rather than changing runtime code to satisfy the test.
- Re-ran the completed regression against the preserved pre-fix hardware ELF. Cleanup injection occurred exactly once; fatal_active was zero and execution stopped at exit's WFE instruction. The corrected ELF returns error 99 and restores VBAR.
- Moved the player setjmp boundary into the outer entry function so it covers execution and compiler cleanup; reset fatal_active on every return. Fixed the diagnostic's rejected-vector return. No extra fallback execution or heap cleanup after fatal corruption.
- Default and JIT worker builds pass. JIT/default lifecycle tests pass; success/cancellation restore executable permissions, and all 240 JIT comparisons pass at three addresses. Native launcher settings tests pass under ASan/UBSan.
- Ran crapper/dryer/mutator on isolated exact copies of the three build adapters. Crapper reports prepare CC4 with no coverage claim; no duplicate candidates at0.8. Added direct tests of the production instruction audit without running build side effects.
- Executed six instruction-audit mutations: initially5killed/1survived. The survivor exposed a mock that ignored subprocess text/bytes semantics; corrected it. Final6/6killed; measured instruction-audit function coverage100%,CC8,CRAP8.0. These metrics apply only to that Python function.
- Mutation worker copies were removed by the tool; the workers directory is empty. Retain logs, coverage and fixtures for reproducibility. No user worktree or installed Amiga file was changed.
