# 0.5.5 combined/batched JIT evidence

See [the report](../../../../../docs/amiga-uae4arm-jit-batch.md).
Hardware logs are from sequential fresh-process A4000TX/ZZ9000 runs. Model/native
checks are separate; neither proves physical execution. `measurements.json`
contains the two-run headless samples and single live samples.

`normal-model.log` retains an inapplicable high-vector test failure: the compatible
68000 does not install the accelerated player's vector guard. Its applicable
lifecycle cases pass in `normal-lifecycle.log`; no production fix was made for
this test invocation. Accelerated rejection/recovery cases pass separately.

Build manifests describe the original workspace inputs. Paths are sanitised;
standalone source hashes are in `docs/source-sha256.json`. No ROMs, disk images,
private preferences, raw MCP responses or signing secrets are included.
