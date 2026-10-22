"""Publish a completed wide run and regenerate its README projection.

This is an explicit publication command, not a background scheduler. Archived
results are immutable: a conflicting destination is refused, not overwritten.
"""

import hashlib
import json
import shutil
from pathlib import Path


def publish(source: Path, destination: Path) -> None:
    rows = json.loads((source / "summary.json").read_text(encoding="utf-8"))
    selection = json.loads((source / "selection.json").read_text(encoding="utf-8"))
    keys = [r["candidate"]["key"] for r in rows]
    if len(keys) != len(set(keys)) or set(keys) != set(selection["ranking"]):
        raise ValueError("Incomplete or duplicate ranking")
    if not set(selection["selected"]) <= set(keys):
        raise ValueError("Finalist missing from results")
    for row in rows:
        if row["candidate"]["key"] in selection["selected"]:
            if len(row["levels"]) < 3 or "phase64" not in row:
                raise ValueError("Finalist refinement has not finished")
    files = [p for p in source.iterdir() if p.is_file()]
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    # Safe rerender of identical archived input; never replace changed data.
    if destination.exists():
        for filename, digest in hashes.items():
            target = destination / filename
            if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError("Archive differs; choose a fresh publication directory")
    else:
        shutil.copytree(source, destination)
    (destination / "publication.json").write_text(
        json.dumps(dict(source=str(source), sha256=hashes), indent=2), encoding="utf-8"
    )


def main(destination: Path | None = None):
    from ballistic_lab.reporting.dc_wide import FOLDER
    from ballistic_lab.reporting.dc_wide import main as render

    target = FOLDER if destination is None else destination
    publish(Path("runs/dc-wide"), target)
    render(target)


if __name__ == "__main__":
    main()
