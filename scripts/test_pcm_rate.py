#!/usr/bin/env python3
"""Native rate-policy checks; does not establish device playback quality."""
from pathlib import Path
import subprocess,tempfile
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as work:
    output=Path(work)/"rate-test"
    subprocess.run(["cc","-std=c99","-Wall","-Wextra","-Werror","-fsanitize=address,undefined","-I"+str(root/"amiga/uae4arm"),str(root/"tests/amiga/uae4arm/audio_rate.c"),"-o",str(output)],check=True)
    subprocess.run([str(output)],check=True)
