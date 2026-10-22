"""Orchestrate a validated topology comparison; physics and plotting live elsewhere."""

import json
from dataclasses import asdict
from pathlib import Path

from ballistic_lab.geometry.families import REFERENCE
from ballistic_lab.models import Candidate, SearchPlan
from ballistic_lab.paths import OUT
from ballistic_lab.reporting.families import plot_results
from ballistic_lab.search.families import search_families, validate_candidates
from ballistic_lab.transport.backend import CudaBackend
from ballistic_lab.validation.receipts import model_fingerprint, require_validation


def main() -> None:
    require_validation(OUT)
    plan = SearchPlan()
    backend = CudaBackend()
    root = Path(__file__).resolve().parents[2]
    previous = json.loads((root / "results/2026-10-22/robust-frozen.json").read_text())
    candidates = [
        Candidate("Reference cross approximation", "cross", tuple(REFERENCE)),
        Candidate("Prior learned triangle", "triangle", tuple(previous["geometry"][3])),
    ]
    discovered, training = search_families(plan, backend)
    candidates.extend(discovered)
    frozen = [candidate.to_record() for candidate in candidates]
    (OUT / "families-frozen.json").write_text(json.dumps(frozen, indent=2))
    validation = validate_candidates(candidates, plan, backend)
    result = dict(
        scope="Topology comparison in a classical angular-response proxy; not paper reproduction",
        model_fingerprint=model_fingerprint(),
        plan=asdict(plan),
        budget_per_family_per_repeat=plan.budget,
        repeats=plan.repeats,
        finalists=frozen,
        training=training,
        validation=validation,
    )
    (OUT / "families-results.json").write_text(json.dumps(result, indent=2))
    plot_results(result, OUT)
    print("Finished: frozen candidates evaluated without reselection.", flush=True)


if __name__ == "__main__":
    main()
