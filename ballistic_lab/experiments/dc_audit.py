"""Audit the published scoring before widening the quantum search."""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from ballistic_lab.experiments.dc_search import evaluate, initial_candidates
from ballistic_lab.validation.dc_score import PairCurrentOracle, oracle_cycle


def main():
    output = Path("runs/dc-audit")
    output.mkdir(parents=True, exist_ok=False)
    source = Path("results/2026-10-22-dc-search")
    rows = json.loads((source / "summary.json").read_text(encoding="utf-8"))
    audit = []
    for key in ("D00", "triangle-control", "triangle-feedback"):
        row = next(r for r in rows if r["candidate"]["key"] == key)
        with gzip.open(source / f"{key}.json.gz", "rt", encoding="utf-8") as stream:
            archive = json.load(stream)
        cache = {round(r["energy_ev"], 12): r for r in archive["spectrum"]}
        spectrum = [
            cache[round(float(e), 12)] for e in np.linspace(0.42, 1.38, row["levels"][-1]["count"])
        ]
        oracle = oracle_cycle(PairCurrentOracle.from_spectrum(spectrum))
        production = row["phase64"]
        difference = abs(oracle["dc_v"] - production["dc_v"])
        passed = difference <= 1e-10 + 0.001 * abs(production["dc_v"])
        assert passed, (key, difference)
        audit.append(
            dict(
                candidate=key,
                production=production,
                independent=oracle,
                difference_v=difference,
                passed=passed,
            )
        )
        print(
            f"{key}: independent {oracle['dc_v'] * 1e6:.7g} uV; difference {difference * 1e9:.5g} nV",
            flush=True,
        )
    # Remove the reference identifier so the evaluator must rebuild and solve,
    # rather than entering the special archived-control cache path.
    item = next(r for r in initial_candidates() if r["key"] == "D00")
    item = dict(item, key="anonymous-reference", origin="fresh quantum score canary")
    fresh = evaluate(item, output=output)
    prior = next(r for r in rows if r["candidate"]["key"] == "D00")["levels"][0]
    difference = abs(fresh["levels"][0]["dc_v"] - prior["dc_v"])
    assert difference < 1e-12, difference
    # The declared score is squared mean voltage / R, irrespective of polarity.
    for row in rows:
        for level in row["levels"]:
            assert np.isclose(level["dc_power_w"], level["dc_v"] ** 2 / 1e4, rtol=1e-12, atol=0)
    ordering = sorted(rows, key=lambda r: (-r["levels"][0]["dc_power_w"], r["candidate"]["key"]))
    assert [r["candidate"]["key"] for r in ordering] == json.loads(
        (source / "selection.json").read_text(encoding="utf-8")
    )["ranking"]
    record = dict(
        independent=audit,
        anonymous_reference_difference_v=difference,
        ranking_and_score_passed=True,
        inputs={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob("*.json*")},
        source={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), Path("ballistic_lab/validation/dc_score.py"))
        },
    )
    (output / "audit.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print("Audit passed, including anonymous fresh quantum reference.", flush=True)


if __name__ == "__main__":
    main()
