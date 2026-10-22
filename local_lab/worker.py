"""Twenty-four local mutations, separate from the matched search campaign."""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.pipeline.dc_continuous import save, single_worker

ROOT = Path("runs/winner-local")


def proposals(parent: dict, seed: int = 221053) -> list[dict]:
    """Eight Gaussian mutations at each of 0.5%, 1%, 2% parameter-range scale."""
    rng = np.random.default_rng(seed)
    bounds = np.asarray(FAMILIES[parent["family"]].bounds)
    low, width = bounds[:, 0], bounds[:, 1] - bounds[:, 0]
    unit = (np.asarray(parent["parameters"]) - low) / width
    children = []
    for scale in (0.005, 0.01, 0.02):
        for index in range(8):
            moved = unit + rng.normal(0, scale, len(unit))
            values = low + (1 - abs(np.mod(moved, 2) - 1)) * width
            children.append(
                dict(
                    key=f"local-s{scale:g}-{index}",
                    family=parent["family"],
                    parameters=values.tolist(),
                    origin=f"mutation of {parent['key']}",
                    parent_key=parent["key"],
                    scale=scale,
                    obstacles=[p.tolist() for p in geometry(parent["family"], values)],
                )
            )
    return children


def sources() -> dict:
    paths = [p for p in Path("ballistic_lab").rglob("*.py") if "reporting" not in p.parts]
    paths += list(Path("local_lab").glob("*.py"))
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def status(**fields):
    save(
        ROOT / "status.json",
        dict(pid=os.getpid(), utc=datetime.now(timezone.utc).isoformat(), **fields),
    )


def run():
    from ballistic_lab.experiments.dc_search import evaluate

    ROOT.mkdir(parents=True, exist_ok=True)
    with single_worker(ROOT):
        manifest = sources()
        path = ROOT / "source.json"
        if path.exists() and json.loads(path.read_text()) != manifest:
            raise RuntimeError("Source changed; start a new explicitly versioned local experiment")
        save(path, manifest)
        plan_path = ROOT / "plan.json"
        if not plan_path.exists():
            snapshot_path = sorted(Path("runs/dc-continuous").glob("round-*.json"))[-1]
            snapshot = json.loads(snapshot_path.read_text())
            eligible = [
                r
                for rows in snapshot["histories"].values()
                for r in rows
                if r.get("energy_converged") and r.get("phase_converged")
            ]
            parent = max(eligible, key=lambda r: r["phase64"]["dc_power_w"])["candidate"]
            save(
                plan_path,
                dict(
                    parent=parent,
                    children=proposals(parent),
                    snapshot=str(snapshot_path),
                    snapshot_sha256=hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),
                    seed=221053,
                    finalists=4,
                ),
            )
        plan = json.loads(plan_path.read_text())
        output = ROOT / "spectra"
        output.mkdir(exist_ok=True)
        results_path = ROOT / "results.json"
        results = json.loads(results_path.read_text()) if results_path.exists() else {}

        def stopped():
            if sources() != manifest:
                raise RuntimeError("Loaded source changed")
            if (ROOT / "STOP").exists():
                status(phase="stopped")
                return True
            return False

        def solve(item, counts):
            key = item["key"]
            if results.get(key, {}).get("unresolved"):
                return
            try:
                results[key] = evaluate(item, counts, output=output)
            except Exception as exc:
                results[key] = dict(candidate=item, unresolved=f"{type(exc).__name__}: {exc}")
            save(results_path, results)

        for item in [plan["parent"]] + plan["children"]:
            if stopped():
                return
            if item["key"] not in results:
                status(phase="screen", candidate=item["key"], completed=len(results), planned=25)
                solve(item, (257,))
        valid = [
            r for k, r in results.items() if k != plan["parent"]["key"] and not r.get("unresolved")
        ]
        selected = sorted(
            valid, key=lambda r: (-r["levels"][0]["dc_power_w"], r["candidate"]["key"])
        )[: plan["finalists"]]
        for item in [plan["parent"]] + [r["candidate"] for r in selected]:
            for count in (513, 1025, 2049, 4097):
                if stopped():
                    return
                row = results[item["key"]]
                if row.get("unresolved") or (
                    row.get("energy_converged") and row.get("phase_converged")
                ):
                    break
                status(phase="refine", candidate=item["key"], grid=count)
                solve(item, (count,))
        status(
            phase="complete",
            screened=len(plan["children"]),
            finalists=len(selected),
            converged=sum(
                bool(r.get("energy_converged") and r.get("phase_converged"))
                for r in results.values()
            ),
            unresolved=sum(bool(r.get("unresolved")) for r in results.values()),
        )


if __name__ == "__main__":
    run()
