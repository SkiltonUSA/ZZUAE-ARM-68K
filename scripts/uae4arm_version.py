"""Read the shared ZZUAE product version used by C and packaging tools."""
from pathlib import Path
import re

HEADER = Path(__file__).resolve().parents[1] / 'amiga/uae4arm/version.h'
VERSION = re.search(
    r'^#define ZU_VERSION "(\d+\.\d+\.\d+(?:-(?:dev|beta\.\d+|rc\.\d+))?)"$',
    HEADER.read_text(), re.MULTILINE,
)
if VERSION is None:
    raise ValueError(f'Invalid ZZUAE version in {HEADER}')
VERSION = VERSION.group(1)
