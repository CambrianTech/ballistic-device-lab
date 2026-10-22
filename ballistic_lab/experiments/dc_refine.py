"""Automatic bounded refinement of every unresolved selected DC finalist."""

import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ballistic_lab.experiments.dc_search import OUTPUT, evaluate


def refine(row):
    for count in (2049, 4097):
        if row.get("energy_converged") and row.get("phase_converged"):
            break
        row = evaluate(row["candidate"], (count,))
    return row


def main():
    source = OUTPUT / "summary.json"
    original = source.read_bytes()
    rows = json.loads(original)
    selected = json.loads((OUTPUT / "selection.json").read_text(encoding="utf-8"))["selected"]
    targets = [r for r in rows if r["candidate"]["key"] in selected]
    manifest = dict(
        rule="Refine every unresolved selected finalist to 2049 then 4097; stop on both gates passing; no new candidates",
        original_summary_sha256=hashlib.sha256(original).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        targets=[r["candidate"]["key"] for r in targets],
    )
    target = OUTPUT / "refinement-manifest.json"
    if target.exists():
        raise RuntimeError("Preserve the first refinement receipt")
    target.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (OUTPUT / "initial-summary.json").write_bytes(original)
    with ProcessPoolExecutor(max_workers=2) as pool:
        updates = list(pool.map(refine, targets))
    lookup = {r["candidate"]["key"]: r for r in updates}
    result = [lookup.get(r["candidate"]["key"], r) for r in rows]
    source.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
