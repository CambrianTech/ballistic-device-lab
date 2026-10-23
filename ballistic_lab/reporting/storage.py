"""Lossless disk drain for immutable continuous-report history copies.

Hard links preserve every historical path and byte. Never use this for mutable
worker checkpoints, spectra, or generated figures. Run as a standalone module
after a fresh checkout; publication also shares existing immutable archives.
"""

import filecmp
import os
import re
import shutil
import uuid
from pathlib import Path

IMMUTABLE = re.compile(r"(?:round-\d{6}|\d{6}-(?:elite|diversity|random)-proposals)\.json\Z")


def share(source: Path, target: Path) -> int:
    """Atomically replace an identical copy with a link; reject conflicts."""
    if target.exists():
        if source.samefile(target):
            return 0
        if not filecmp.cmp(source, target, shallow=False):
            raise ValueError(f"Archive conflict: {target}")
    size = target.stat().st_size if target.exists() else 0
    temporary = target.with_name(target.name + f".{uuid.uuid4().hex}.link")
    try:
        os.link(source, temporary)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return size


def archive(source: Path, target: Path) -> None:
    """Copy once, then share only immutable report records across snapshots."""
    if target.exists():
        if not filecmp.cmp(source, target, shallow=False):
            raise ValueError(f"Archive conflict: {target}")
        return
    if IMMUTABLE.fullmatch(source.name):
        for existing in sorted(target.parent.parent.glob(f"round-*/{source.name}")):
            if not filecmp.cmp(source, existing, shallow=False):
                raise ValueError(f"Archive conflict: {existing}")
            share(existing, target)
            return
    shutil.copyfile(source, target)


def drain(root: Path) -> dict:
    """Deduplicate immutable history within this exact report directory only."""
    root = root.resolve(strict=True)
    canonical = {}
    reclaimed = 0
    linked = 0
    for directory in sorted(root.glob("round-*")):
        if directory.is_symlink() or directory.resolve().parent != root:
            raise ValueError(f"Unsafe report directory: {directory}")
        for path in sorted(directory.glob("*.json")):
            if not IMMUTABLE.fullmatch(path.name):
                continue
            if path.is_symlink() or path.resolve().parent != directory.resolve():
                raise ValueError(f"Unsafe report file: {path}")
            first = canonical.setdefault(path.name, path)
            saved = share(first, path)
            reclaimed += saved
            linked += bool(saved)
    return {"reclaimed_bytes": reclaimed, "consolidated_files": linked}


if __name__ == "__main__":
    print(drain(Path("results/continuous-dc")))
