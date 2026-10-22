"""Audit-gated wider direct-DC search with automatic finalist refinement."""

import hashlib
import json
import shutil
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from functools import partial
from pathlib import Path

from ballistic_lab.experiments.dc_search import evaluate, initial_candidates
from ballistic_lab.search.dc_space import WideDCPlan, proposals

OUTPUT = Path("runs/dc-wide")


def refine(item):
    row = evaluate(item, (257, 513, 1025), output=OUTPUT)
    for count in (2049, 4097):
        if row.get("energy_converged") and row.get("phase_converged"):
            break
        row = evaluate(item, (count,), output=OUTPUT)
    return row


def main():
    audit_path = Path("runs/dc-audit/audit.json")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if not audit["ranking_and_score_passed"] or not all(r["passed"] for r in audit["independent"]):
        raise RuntimeError("Scoring audit has not passed")
    plan = WideDCPlan()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    controls = [r for r in initial_candidates() if r["key"] in ("D00", "D14", "triangle-control")]
    manifest = dict(
        plan=asdict(plan),
        controls=controls,
        objective="DC power at 10 mV peak into 10 kohm; fixed-potential, 0.9 eV, 300 K",
        selection="top two fresh-search candidates per repeat plus fixed triangle and D00; refine all through at most 4097 energies",
        audit_sha256=hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        source={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("ballistic_lab").rglob("*.py")
        },
    )
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    # Preserve exact frozen controls and their spectra, then independently
    # recompute metrics and gates via the same evaluator as fresh candidates.
    for item in controls:
        shutil.copyfile(
            Path("results/2026-10-22-dc-search") / f"{item['key']}.json.gz",
            OUTPUT / f"{item['key']}.json.gz",
        )
    rows = []
    run = partial(evaluate, output=OUTPUT)
    with ProcessPoolExecutor(max_workers=plan.workers) as pool:
        rows = list(pool.map(run, controls))
        for round_index in range(plan.feedback_rounds + 1):
            batch = [
                item
                for repeat in range(len(plan.seeds))
                for item in proposals(plan, repeat, round_index, rows)
            ]
            (OUTPUT / f"proposals-{round_index}.json").write_text(
                json.dumps(batch, indent=2), encoding="utf-8"
            )
            rows += list(pool.map(run, batch))
            (OUTPUT / "screen-summary.json").write_text(
                json.dumps(rows, indent=2), encoding="utf-8"
            )
        selected = {"D00", "triangle-control"}
        for repeat in range(len(plan.seeds)):
            ranking = sorted(
                (r for r in rows if r["candidate"].get("repeat") == repeat),
                key=lambda r: (-r["levels"][0]["dc_power_w"], r["candidate"]["key"]),
            )
            selected.update(r["candidate"]["key"] for r in ranking[:2])
        ranking = sorted(rows, key=lambda r: (-r["levels"][0]["dc_power_w"], r["candidate"]["key"]))
        (OUTPUT / "selection.json").write_text(
            json.dumps(
                dict(ranking=[r["candidate"]["key"] for r in ranking], selected=sorted(selected)),
                indent=2,
            ),
            encoding="utf-8",
        )
        updates = list(
            pool.map(refine, [r["candidate"] for r in rows if r["candidate"]["key"] in selected])
        )
    lookup = {r["candidate"]["key"]: r for r in updates}
    result = [lookup.get(r["candidate"]["key"], r) for r in rows]
    (OUTPUT / "summary.json").write_text(
        json.dumps(result, indent=2, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
