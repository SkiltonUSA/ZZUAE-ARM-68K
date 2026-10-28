# Source backup and build scope

This backup contains the ZZUAE port, launcher, input/audio code, tests, upstream
patch preparation scripts and the shared runtime files required by those builds.
Shared dependencies are organized under `amiga/uae4arm/support/`:
`allocator` (heap), `core1` (worker/MMU), `memory` (scalar copy/fill), and `libc`
(linker layout and library configuration). Exported scripts use these ZZUAE
paths; the parent workspace retains its shared source locations.

The existing build expects Podman, the `nuflix-converter-root` connection and
`zzffmpeg-toolchain` container mounted at `/work`, Arm Embedded GCC 15.3.1,
picolibc headers, a PIC soft-float libc archive, and Homebrew LLVM/lld. ImageMagick converts the included artwork. The 68K
compiler image is pinned in `amiga/upstream.json`. A clean-machine toolchain
bootstrap is not yet packaged; the source backup is not a one-command installer.

See `amiga/uae4arm/README.md` for the core/player build sequence. Build the
launcher using `python3 scripts/build_uae4arm_launcher.py`.
The exported `scripts/amiga.py` is a small compiler-pin adapter; it does not
include the unrelated workspace/bridge management commands.

Native input check:

```sh
mkdir -p .context/tests
cc -std=c99 -fsanitize=address,undefined -Iamiga/uae4arm tests/amiga/uae4arm/joystick.c -o .context/tests/joystick
.context/tests/joystick
```

ARM instruction-model tests require Unicorn and prepared build outputs. Hardware
validation is separate. The old parent-workspace `make test-amiga*` targets in
historical reports are not included in this standalone backup.

`docs/source-sha256.json` records exported source hashes. Build manifests and
selected logs are retained under `docs/verification`. The public repository does
not contain Kickstart ROMs or game disks. Packaged binaries are available on the
GitHub Releases page, with an installer guide and corresponding source bundle.

## 0.5.5 experimental player

The package uses the combined/batched flags documented in
[the 0.5.5 report](amiga-uae4arm-jit-batch.md#build). Use that build directory as
`build_uae4arm_fpu.py --base DIRECTORY --hardware` to build the matching optional
FPU player. The compatible player still uses the normal build sequence.

Native dispatcher regression: `python3 tests/amiga/uae4arm/test_jit_batch_prepare.py`.
Pass `--cache32` to the ARM lifecycle harness for the 64 MiB experimental runtime.
The incompatible high-vector rejection and JIT cleanup-injection cases apply to
the accelerated players; the compatible player does not install that JIT guard.

Native DF1, read-light and clock checks:

```sh
for test in disk_light second_disk rtc; do
  cc -std=c99 -fsanitize=address,undefined -Iamiga/uae4arm tests/amiga/uae4arm/$test.c -o .context/tests/$test
  .context/tests/$test
done
```

After preparing the pinned upstream source, run
`python3 tests/amiga/uae4arm/test_disk_activity.py` for the real FIFO reader.
The ARM model accepts `--df1 --rtc` to verify the second image and mapped clock.
