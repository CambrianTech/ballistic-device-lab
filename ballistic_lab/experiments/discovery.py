"""Expanded geometry search, holdout evaluation, and normalized tolerance screening."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.metrics.angular import measure_response
from ballistic_lab.models import Candidate, RayConfig, SearchPlan
from ballistic_lab.paths import OUT
from ballistic_lab.search.discovery import DiscoveryPlan, discover
from ballistic_lab.search.families import validate_candidates
from ballistic_lab.transport.backend import CudaBackend
from ballistic_lab.validation.receipts import model_fingerprint, require_validation


def main() -> None:
    require_validation(OUT)
    if (OUT / "discovery-results.json").exists():
        raise RuntimeError("Use a fresh output directory; discovery results already exist")
    root = Path(__file__).resolve().parents[2]
    prior = json.loads((root / "results/2026-10-22-refinement/refinement-frozen.json").read_text())[
        9
    ]
    control = Candidate("Beveled refinement anchor", prior["family"], tuple(prior["x"]))
    plan, backend = DiscoveryPlan(), CudaBackend()
    found, training = discover(plan, backend)
    candidates = [control] + found
    frozen = [c.to_record() for c in candidates]
    (OUT / "discovery-frozen.json").write_text(json.dumps(frozen, indent=2))
    validation_plan = SearchPlan()
    validation = validate_candidates(candidates, validation_plan, backend, seed_base=820000)
    tolerances = []
    for index, candidate in enumerate(candidates):
        limits = np.asarray(FAMILIES[candidate.family].bounds)
        rng = np.random.default_rng(920000 + index)
        values = np.asarray(candidate.parameters) + rng.normal(0, 0.01, (16, len(limits))) * (
            limits[:, 1] - limits[:, 0]
        )
        # Restrict to the same guaranteed-valid family construction domain.
        values = np.clip(values, limits[:, 0], limits[:, 1])
        scores = measure_response(
            [geometry(candidate.family, x) for x in values], backend, RayConfig(count=32768), 890000
        ).derivative
        nominal = measure_response(
            [geometry(candidate.family, np.asarray(candidate.parameters))],
            backend,
            RayConfig(count=32768),
            890000,
        ).derivative[0]
        tolerances.append(
            dict(
                candidate=index,
                x=values.tolist(),
                scores=scores.tolist(),
                nominal=float(nominal),
                mean=float(scores.mean()),
                minimum=float(scores.min()),
            )
        )
    result = dict(
        scope="Expanded classical geometry screen; no novelty or efficiency claim",
        model_fingerprint=model_fingerprint(),
        plan=asdict(plan),
        validation_plan=asdict(validation_plan),
        validation_seed_base=820000,
        finalists=frozen,
        training=training,
        validation=validation,
        tolerances=tolerances,
    )
    (OUT / "discovery-results.json").write_text(json.dumps(result, indent=2))
    print("Complete: all finalists held out and tolerance-screened.", flush=True)


if __name__ == "__main__":
    main()
