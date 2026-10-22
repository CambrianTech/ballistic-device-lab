"""Reproducible refinement experiment with frozen candidates and fresh holdout."""

import json
from dataclasses import asdict
from pathlib import Path

from ballistic_lab.models import Candidate, SearchPlan
from ballistic_lab.paths import OUT
from ballistic_lab.search.families import validate_candidates
from ballistic_lab.search.refinement import RefinementPlan, refine
from ballistic_lab.transport.backend import CudaBackend
from ballistic_lab.validation.receipts import model_fingerprint, require_validation


def main() -> None:
    require_validation(OUT)
    root = Path(__file__).resolve().parents[2]
    previous = json.loads((root / "results/2026-10-22-families/families-frozen.json").read_text())
    # Existing anchors, declared before new simulation: prior triangle and
    # best training-selected bevel from the previous experiment (not holdout selection).
    anchors = [Candidate(p["name"], p["family"], tuple(p["x"])) for p in (previous[1], previous[9])]
    plan = RefinementPlan()
    backend = CudaBackend()
    discovered, training = refine(anchors, plan, backend)
    finalists = anchors + discovered
    frozen = [candidate.to_record() for candidate in finalists]
    (OUT / "refinement-frozen.json").write_text(json.dumps(frozen, indent=2))
    validation_plan = SearchPlan(scattering_ratios=(0.5, 1.0, 2.0), specularities=(0.8,))
    validation = validate_candidates(finalists, validation_plan, backend, seed_base=270000)
    result = dict(
        scope="Angular steering proxy; not electrical conversion efficiency",
        model_fingerprint=model_fingerprint(),
        plan=asdict(plan),
        validation_plan=asdict(validation_plan),
        validation_seed_base=270000,
        finalists=frozen,
        training=training,
        validation=validation,
    )
    (OUT / "refinement-results.json").write_text(json.dumps(result, indent=2))
    print("Finished: all frozen candidates retained in fresh-seed evaluation.", flush=True)


if __name__ == "__main__":
    main()
