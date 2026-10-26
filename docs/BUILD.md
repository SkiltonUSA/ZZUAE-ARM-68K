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
