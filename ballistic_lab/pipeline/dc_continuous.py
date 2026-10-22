"""Persistent, resumable three-arm DC search. Monitoring does not drive compute.

Run with the Kwant interpreter. Create runs/dc-continuous/STOP to stop after the
current batch. No automatic git writes; the agent publishes completed snapshots.
"""

import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from ballistic_lab.search.dc_space import WideDCPlan, proposals

ROOT = Path("runs/dc-continuous")
ARMS = ("elite", "diversity", "random")


def save(path: Path, value: dict | list) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


@contextmanager
def single_worker(root: Path):
    """OS-released lock survives crashes without stale PID assumptions."""
    with (root / "worker.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def batch(arm: str, round_index: int, history: list[dict]) -> list[dict]:
    # Keep global proposals and the initial seed set matched across arms.
    plan = replace(WideDCPlan(), parent_strategy=arm, mutation_floor=0.02)
    items = [
        item
        for repeat in range(len(plan.seeds))
        for item in proposals(plan, repeat, round_index, history)
    ]
    return [dict(item, key=f"{arm}-{item['key']}", arm=arm) for item in items]


def finalists(history: list[dict]) -> list[dict]:
    """Equal refinement allocation: best two screening candidates per arm."""
    return sorted(history, key=lambda r: (-r["levels"][0]["dc_power_w"], r["candidate"]["key"]))[:2]


def task(item: dict, output: Path, refine: bool) -> dict:
    from ballistic_lab.experiments.dc_search import evaluate

    row = evaluate(item, (257, 513, 1025) if refine else (257,), output=output)
    if refine:
        for count in (2049, 4097):
            if row.get("energy_converged") and row.get("phase_converged"):
                break
            row = evaluate(item, (count,), output=output)
    return row


def status(root: Path, **fields) -> None:
    save(
        root / "status.json",
        dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat(), **fields),
    )


def initialize(root: Path) -> dict:
    source = Path("results/2026-10-22-dc-wide")
    audit_path = Path("results/2026-10-22-dc-audit/audit.json")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if not audit["ranking_and_score_passed"] or not all(r["passed"] for r in audit["independent"]):
        raise RuntimeError("Independent scoring audit has not passed")
    source_rows = json.loads((source / "summary.json").read_text(encoding="utf-8"))
    # Identical starting population: only the 40 round-zero proposals, no controls.
    initial = [r for r in source_rows if r["candidate"].get("round") == 0]
    initial = [
        dict(r, levels=r["levels"][:1], energy_converged=False, phase_converged=False)
        for r in initial
    ]
    for row in initial:
        row.pop("phase64", None)
    if len(initial) != 40:
        raise ValueError("Unexpected initial population")
    output = root / "spectra"
    output.mkdir(exist_ok=True)
    # Copy spectra for free reuse but preserve the coarse-only starting evidence.
    import gzip

    for row in initial:
        key = row["candidate"]["key"]
        with gzip.open(source / f"{key}.json.gz", "rt", encoding="utf-8") as handle:
            record = json.load(handle)
        record.update(row)
        with gzip.open(output / f"{key}.json.gz", "wt", encoding="utf-8") as handle:
            json.dump(record, handle, allow_nan=False)
    state = dict(
        round=1,
        histories={arm: initial for arm in ARMS},
        completed=[],
        baseline_source=str(source),
        objective="DC power at fixed 10 mV peak and 10 kohm",
        note="Equal proposal and finalist-count budgets; record actual solver work separately. Fixed internal potential.",
        audit_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),
    )
    save(root / "state.json", state)
    return state


def run(root: Path = ROOT, workers: int = 4) -> None:
    root.mkdir(parents=True, exist_ok=True)
    with single_worker(root):
        # Refuse mixing different physics/search implementations in a resumed campaign.
        files = [p for p in Path("ballistic_lab").rglob("*.py") if "reporting" not in p.parts]
        hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        manifest = root / "source.json"
        if manifest.exists() and json.loads(manifest.read_text(encoding="utf-8")) != hashes:
            raise RuntimeError("Source changed: archive this campaign before starting another")
        save(manifest, hashes)
        state_path = root / "state.json"
        state = (
            json.loads(state_path.read_text(encoding="utf-8"))
            if state_path.exists()
            else initialize(root)
        )
        try:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                while not (root / "STOP").exists():
                    index = state["round"]
                    for arm in ARMS:
                        history = state["histories"][arm]
                        proposal_file = root / f"{index:06d}-{arm}-proposals.json"
                        if proposal_file.exists():
                            items = json.loads(proposal_file.read_text(encoding="utf-8"))
                        else:
                            items = batch(arm, index, history)
                            save(proposal_file, items)
                        for stage in ("screen", "refine"):
                            token = f"{index}:{arm}:{stage}"
                            if token in state["completed"]:
                                continue
                            known = {r["candidate"]["key"]: r for r in history}
                            candidates = (
                                items
                                if stage == "screen"
                                else [r["candidate"] for r in finalists(history)]
                            )
                            if stage == "screen":
                                candidates = [c for c in candidates if c["key"] not in known]
                            status(
                                root, phase=stage, round=index, arm=arm, remaining=len(candidates)
                            )
                            futures = {
                                pool.submit(task, c, root / "spectra", stage == "refine"): c
                                for c in candidates
                            }
                            for future in as_completed(futures):
                                row = future.result()
                                known[row["candidate"]["key"]] = row
                                history = list(known.values())
                                state["histories"][arm] = history
                                save(state_path, state)
                                status(
                                    root,
                                    phase=stage,
                                    round=index,
                                    arm=arm,
                                    last_completed=row["candidate"]["key"],
                                )
                            state["completed"].append(token)
                            save(state_path, state)
                            if (root / "STOP").exists():
                                status(root, phase="stopped", round=index)
                                return
                    # Only full matched rounds become immutable reportable snapshots.
                    save(root / f"round-{index:06d}.json", state)
                    state["round"] += 1
                    save(state_path, state)
                status(root, phase="stopped", round=state["round"])
        except Exception as error:
            status(root, phase="failed", error=repr(error), round=state["round"])
            raise


if __name__ == "__main__":
    run()
