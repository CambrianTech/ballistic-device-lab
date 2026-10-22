"""Equal-budget sampling and frozen-candidate evaluation."""

import numpy as np

from ballistic_lab.geometry.families import geometry, sample
from ballistic_lab.metrics.angular import measure_response
from ballistic_lab.models import Candidate, RayConfig, SearchPlan, TransportBackend


def search_families(
    plan: SearchPlan, backend: TransportBackend
) -> tuple[list[Candidate], list[dict]]:
    candidates, records = [], []
    for repeat in range(plan.repeats):
        for family in ("triangle", "beveled", "cross"):
            rng = np.random.default_rng(14000 + repeat)
            parameters = sample(family, rng, plan.budget)
            geometries = [geometry(family, values) for values in parameters]
            response = measure_response(
                geometries,
                backend,
                RayConfig(count=plan.training_rays),
                15000 + repeat * 10,
            )
            best = int(np.argmax(response.derivative))
            candidates.append(
                Candidate(f"{family} search {repeat + 1}", family, tuple(parameters[best]))
            )
            records.append(
                dict(
                    repeat=repeat,
                    family=family,
                    x=parameters.tolist(),
                    scores=response.derivative.tolist(),
                )
            )
            print(
                f"{repeat + 1} {family}: training best {response.derivative[best]:.6f}",
                flush=True,
            )
    return candidates, records


def validate_candidates(
    candidates: list[Candidate],
    plan: SearchPlan,
    backend: TransportBackend,
    seed_base: int = 60000,
) -> list[dict]:
    """No ranking or reselection occurs here; all frozen candidates are returned."""
    geometries = [
        geometry(candidate.family, np.asarray(candidate.parameters)) for candidate in candidates
    ]
    validations = []
    for ratio in plan.scattering_ratios:
        for specularity in plan.specularities:
            config = RayConfig(
                count=plan.validation_rays,
                mean_free_path=2 * ratio,
                specularity=specularity,
            )
            responses = [
                measure_response(geometries, backend, config, seed_base + seed * 10)
                for seed in range(plan.validation_seeds)
            ]
            scores = np.array([response.derivative for response in responses])
            tails = np.array([response.p99_path_over_width for response in responses])
            validations.append(
                dict(
                    ratio=ratio,
                    specularity=specularity,
                    score_mean=scores.mean(0).tolist(),
                    seed_std=scores.std(0, ddof=1).tolist(),
                    paired_vs_reference=(scores - scores[:, [0]]).tolist(),
                    mean_p99_path_over_width=tails.mean(0).tolist(),
                )
            )
    return validations
