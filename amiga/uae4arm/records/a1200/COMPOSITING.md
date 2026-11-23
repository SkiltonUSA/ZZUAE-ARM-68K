# A1200 compositing investigation

Following the [conversion-cache experiment](RENDER-REUSE.md), this investigation
moves upstream into guest image drawing. Private builds use the same interpreter,
NEON bitplane/half-width conversion and inline ChipRAM reads as the installed
0.6.0-dev reference. No guest instructions, chipset timing or frame handshakes
are skipped.

The workload is the same 6,000-frame Banshee demo sequence: PAL A1200/68020,
native 320×256 fullscreen and sound output off. Audio hardware remains emulated.
Counts and sampled drawing timers cover frames 3,000–6,000. See
[benchmark method](PERFORMANCE.md). These FPS figures measure emulated frames,
not the game's internal frame rate.

## Drawing profile

| Stage | Estimated share of diagnostic interval |
|---|---:|
| Entire line drawing | 8.28% |
| Planar-to-chunky conversion | 1.40% |
| Palette cache maintenance | 0.11% |
| Sprite composition | 2.30% |
| Colour-change processing, including pixel drawing | 4.00% |
| Palette-to-pixel drawing | 3.81% |

The timers sample one in 64 calls with independent deterministic selectors.
They are inclusive and overlap; do not add the rows. Instrumentation changes
execution cost, so these estimates guide investigation, not speedup claims.

The 768,000 drawn lines all use normal AGA two-pixel stretch, with identity XOR
and mask values. There are 491,520,000 destination pixels. No HAM, EHB,
dual-playfield or mid-line colour changes appear in this measured interval.
All lines have sprite entries. The existing palette cache copies 3,000 times
and hits 765,000 times (99.61%); another palette cache is not justified here.
Other games and Banshee loading/title scenes can use different paths.

[Counts and sampled timers](composite/profile-composite-analysis.json),
[hardware log](composite/profile-run.log),
[diagnostic patch](composite/composite-profile.patch).

## Four-pixel candidate

Only the normal AGA stretch loop changes. When XOR is zero and the mask is 255,
it performs four independent indexed palette lookups and four duplicated RGB565
stores per iteration. The original two-destination-pixel tail preserves source
advance and short/split-span behaviour. Other modes and masked paths stay intact.
No history cache or additional frame buffer is introduced.

Sanitized native comparisons extract both loop implementations from the actual
private sources. All 17,301,504 comparisons pass across every byte XOR/mask,
lengths 0–65, aligned start offsets, odd tails and destination guards. Four ARM
fixtures also match CPU state, RAM, output pixels and frame hashes for memory,
interrupt, beam and Copper colour-write cases. The emitted ARM retains the four
lookups/stores; compiler output was inspected before hardware testing.

[Candidate patch](composite/pixel4.patch),
[native results](composite/native-pixels.log),
[ARM comparisons](composite/model-pixels.log).

## Matched hardware results

| Build/run | Whole-run emulated FPS | Gameplay emulated FPS |
|---|---:|---:|
| Earlier reference | 31.76 | 26.79 |
| Four-pixel candidate | 32.14 | 27.30 |
| Fresh reference | 31.74 | 26.78 |
| Candidate repeat | 32.15 | 27.33 |

The candidate improves gameplay throughput by **1.90%** in the first comparison
and **2.03%** against the fresh control. Whole-run improvement is smaller because
it includes loading and other display paths. This is a repeatable improvement
for this particular workload, not a general 2% gain across all Amiga software.

Both candidate runs and the fresh control completed 6,000 frames with identical
CPU diagnostics (116,472,634 dispatches, 814,003,022 cycles, hash `eef62420`,
PC `00029056`) and final RGB565 SHA256
`78ef0a4ca34c602652f7dbb23f23777f3cba821303411748f399339bcc0be71e`.
The diagnostic run also matched. All four new physical runs—24,000 frames—passed
register/MMU/cache restoration and owned-memory release.

[Matched run data](composite/results.json),
[artifact hashes](composite/builds.json).

## Initial decision and remaining checks

The first pass retained the four-pixel candidate for broader validation. Unlike the previous
conversion cache, this change has demonstrated a small repeatable gain without
new buffer allocations. At that point it was not enabled in installed players or a
release. No game/ROM media or firmware was changed.

Before promotion, test other AGA games and audible playback, then integrate the
patch through the source preparation/build pipeline and rebuild the optional
FPU player from that exact recorded base. The generated `linetoscr.cpp` is
included by `drawing.cpp`; its content must participate in incremental build
fingerprinting to prevent stale objects. Normal/FPU product versions must match.

After the initial pass, installed normal/FPU binaries were unchanged. Private
test executables were removed, and Core1 was checked free. No GitHub push or
release was made during that pass.
[Installation verification](composite/unchanged-installed-players.json).

## Wider validation and source integration

A second pass adds four more 6,000-frame physical runs. Each pair has identical
final CPU diagnostics and pixels, with clean register/MMU/cache restoration and
owned-memory release.

| Workload | Reference FPS | Pixel-loop FPS | Scope |
|---|---:|---:|---|
| Slam Tilt demo, sound output off | 40.86 | 42.11 | Whole loading/intro sequence; not pinball gameplay |
| Banshee demo, Paula | 36.45 | 36.90 | Whole sequence; audio-driven display skipping active |

Slam Tilt's whole-sequence gain is 3.04% in this single matched pair. Banshee's
sound-off gameplay gain remains the independently repeated 1.90–2.03% result.
The Paula figures are not displayed/game FPS: 2,309 and 2,354 frames respectively
were presented out of 6,000 emulated frames. Both builds queued, submitted and
completed 3,330,048 samples at 27,710 Hz with zero device errors. Gap counters
were 2,087 and 2,079. This does not establish better audible quality; the existing
starvation/gap issue remains unresolved.

[Wider measurements](composite/wider/results.json) retain the individual commands,
logs and final-state evidence. No audible listening acceptance was recorded.

The optimisation is now available to the source build as `--aga-pixel-loop`:

```sh
python3 scripts/build_uae4arm_a1200.py --neon-bitplanes --neon-half --chip-reads --aga-pixel-loop
```

Source preparation starts from the pinned upstream pixel file on each build.
Only the normal identity-mask AGA stretch branch changes. Build metadata records
`aga_pixel_loop`; the build directory has a `-pixel4` suffix. The generated
source matches the privately tested candidate, and emitted drawing instructions
match. The 17,301,504 sanitized comparisons also pass against this preparation
function. Other rendering modes retain their existing paths.

A build-cache regression was reproduced first: editing included `linetoscr.cpp`
did not invalidate `drawing.o`. Its contents now participate in that object's
fingerprint. The regression test confirms unchanged inputs reuse the object,
while changed pixel code triggers a rebuild. Four ARM state comparisons and the
direct-display bounds/format/SIMD checks pass on the fully rebuilt normal core.

## Experimental installation

The integrated normal player passed physical PAL and NTSC checks in both a
Workbench window and fullscreen (120 guest frames each). The matching FPU build
passed the physical arithmetic/VFP fixture. ARM model checks also cover FPU On
and Off. Both build manifests report version 0.6.0-dev and the same pixel-loop,
NEON, ChipRAM-read and cache configuration; their drawing objects are identical.

The normal and FPU players were then installed together in the existing
experimental A1200 drawer. The canonical 0.5.7 installation is unchanged.
Local copies of the previous binaries remain available for rollback. No firmware
change, GitHub publication or release package was made.

[Installed artifact hashes](composite/wider/installed-pixel-builds.json),
[physical display/FPU checks](composite/wider/install-tested.log),
[matching build records](composite/wider/builds.json).

One FPU model invocation initially selected normal media instead of its synthetic
ROM fixture; the corrected invocation passed with FPU both enabled and disabled.
This was a harness setup error, not an emulator fix.
