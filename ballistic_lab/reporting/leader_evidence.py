"""Produce independent-score receipts from frozen, already-solved spectra."""

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from ballistic_lab.validation.dc_score import PairCurrentOracle, oracle_cycle


def audit(row, destination):
    key = row["candidate"]["key"]
    source = Path("runs/dc-continuous/spectra") / f"{key}.json.gz"
    if not source.exists():
        source = Path("results/2026-10-22-dc-wide") / f"{key}.json.gz"
    with gzip.open(source, "rt", encoding="utf-8") as stream:
        record = json.load(stream)
    if record["candidate"]["obstacles"] != row["candidate"]["obstacles"]:
        raise ValueError("Audit spectrum geometry mismatch")
    cache = {round(r["energy_ev"], 12): r for r in record["spectrum"]}
    spectrum = [
        cache[round(float(e), 12)] for e in np.linspace(0.42, 1.38, row["levels"][-1]["count"])
    ]
    inputs = dict(
        candidate=row["candidate"],
        spectrum=spectrum,
        production=row["phase64"],
        oracle_source=hashlib.sha256(
            Path("ballistic_lab/validation/dc_score.py").read_bytes()
        ).hexdigest(),
        audit_source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )
    fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    folder = Path("runs/leader-audits")
    folder.mkdir(exist_ok=True)
    receipt = folder / f"{fingerprint}.json"
    if receipt.exists():
        result = json.loads(receipt.read_text())
    else:
        independent = oracle_cycle(PairCurrentOracle.from_spectrum(spectrum))
        difference = abs(independent["dc_v"] - row["phase64"]["dc_v"])
        tolerance = 1e-10 + 0.001 * abs(row["phase64"]["dc_v"])
        result = dict(
            candidate=key,
            fingerprint=fingerprint,
            independent=independent,
            production=row["phase64"],
            difference_v=difference,
            tolerance_v=tolerance,
            passed=difference <= tolerance,
            scope="Independent quadrature and load solver on the same fixed-potential spectrum; not independent physics or experimental validation",
        )
        temporary = receipt.with_suffix(".tmp")
        temporary.write_text(json.dumps(result, indent=2), encoding="utf-8")
        temporary.replace(receipt)
    output = destination / "evidence"
    output.mkdir(exist_ok=True)
    (output / f"{key}-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    # Publish the exact audit input, not just a hash of inaccessible local spectra.
    payload = json.dumps(inputs, allow_nan=False).encode("utf-8")
    (output / f"{key}-input.json.gz").write_bytes(gzip.compress(payload, mtime=0))
    return result


def render(rows, destination):
    results = [audit(row, destination) for row in rows]
    table = ["| Independent score check | Difference (nV) | Result |", "| --- | ---: | --- |"]
    for row in results:
        table.append(
            f"| {row['candidate']} | {row['difference_v'] * 1e9:.4f} | {'Pass' if row['passed'] else 'FAIL — investigate'} |"
        )
    return (
        "\n".join(table)
        + f"\n\n[Audit receipts and exact input spectra]({destination.as_posix()}/evidence). This cross-check uses pair currents, Gaussian quadrature and a separate load solver; it shares the same fixed-potential transport model.\n"
    )
