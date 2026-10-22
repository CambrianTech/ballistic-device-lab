"""Keep generated runs separate from immutable research snapshots."""

import os
from pathlib import Path

OUT = Path(
    os.environ.get("BALLISTIC_OUTPUT_DIR", Path(__file__).resolve().parents[1] / "runs" / "latest")
)
OUT.mkdir(parents=True, exist_ok=True)
