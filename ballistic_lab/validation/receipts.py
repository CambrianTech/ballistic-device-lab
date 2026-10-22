"""Content-addressed validation receipts: stale checks cannot authorize a search."""

import hashlib
import json
from pathlib import Path


def model_fingerprint() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1]
    sources = sorted(root.rglob("*.py")) + sorted(root.rglob("*.cu"))
    return {
        str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sources
    }


def require_validation(output: Path) -> None:
    receipt_path = output / "families-validation.json"
    if not receipt_path.exists():
        raise RuntimeError("Run validate_families.py before searching.")
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("model_fingerprint") != model_fingerprint():
        raise RuntimeError("Run validate_families.py for this exact source before searching.")
