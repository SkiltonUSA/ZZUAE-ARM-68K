"""Compiler pin adapter for the standalone ZZUAE source backup."""
import json
from pathlib import Path
PIN = json.loads((Path(__file__).resolve().parents[1] / "amiga/upstream.json").read_text())
