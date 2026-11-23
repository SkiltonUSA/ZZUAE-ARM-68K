# Fine pixels and mid-line Copper colour checks

This extends the [static AGA fetch test](AGA-FETCH-ORACLE.md). No production
emulator code, player, defaults or firmware changed.

## Results

Ten cases pass in the Cortex-A9 instruction model using the current A1200 ELF:

| Pattern | PAL | NTSC | Checked pixels per final capture |
|---|---|---|---:|
| Individual pixels, FMODE 0 | PASS | PASS | 122,880 |
| Individual pixels, FMODE 1 | PASS | PASS | 122,880 |
| Individual pixels, FMODE 2 | PASS | PASS | 122,880 |
| Individual pixels, FMODE 3 | PASS | PASS | 122,880 |
| Copper colour changes, FMODE 3 | PASS | PASS | 119,360 |

The fine pattern varies colour index for every logical pixel. Unlike the prior
stripe pattern's $00/$ff plane bytes, this exercises bit ordering inside bytes,
words and wide fetches. Expected RGB565 values are calculated independently of
UAE's planar conversion. Reversing eight logical pixels makes the oracle fail
in all eight captures. The earlier eight stripe ROMs remain byte-identical.

The Copper pattern holds index 1 across eight planes. Eleven selected scanlines
use WAIT/MOVE to change COLOR01 from red to green to blue, then restore red before
the next line. The checker requires the correct colours in predefined interior
regions and red across intervening rows. Replacing a green sample with red fails.

These are bounded colour-order checks: transition edges are deliberately excluded,
so they do not prove exact Copper cycle latency or DMA arbitration. No DMA
stop/restart, WAIT/SKIP masking, HAM8 or display-resolution change was added here.
Those remain separate work. No performance or audio improvement is claimed.

## Physical testing

Four FMODE 3 cases now pass on the A4000TX: fine pixels and Copper colours under
both PAL and NTSC. Each completes 120 frames, for 480 frames total. Final captures
match the ARM model byte-for-byte and pass the independent pixel checks:

| Diagnostic | PAL checked pixels | NTSC checked pixels |
|---|---:|---:|
| Individual pixels, FMODE 3 | 122,880 | 122,880 |
| Copper colours, FMODE 3 | 119,360 | 119,360 |

All runs report zero failures, zero register mismatches and zero cache-witness
errors, with owned memory released. Core1 is free after testing. Normal and FPU
player MD5 hashes remain unchanged; the temporary diagnostic ROM and log were
removed. Audio was off. These are correctness checks, not gameplay/FPS tests.
NTSC comparisons locate the pattern at output row 23; they do not validate exact
vertical placement. The Copper transition-edge exclusions above still apply.

The earlier connection failure cleared: Python could connect to the Amiga again,
and restarting the local MCP service with `make amiga-hardware` restored command
access. The original failure's cause was not established. No firmware, startup
or network configuration was changed.

## Run

```sh
.tools/dosbox-model-venv/bin/python tests/amiga/uae4arm/check_aga_events.py \
  /path/to/uae-machine.elf .context/amiga/uae4arm/aga-events
```

Run serially with other machine-model tests because they share a capture path.
The original diagnostic generator is `tests/amiga/uae4arm/aga_fetch_fixture.py`.
[Evidence](aga-events/) contains model and physical logs, results, source hashes
and the earlier connection failure. It contains no Kickstart or game media.
