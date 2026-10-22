"""Population search across broader shape spaces, with an equal-cost random arm."""

from dataclasses import dataclass

import numpy as np

from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.metrics.angular import measure_response
from ballistic_lab.models import Candidate, RayConfig, TransportBackend


@dataclass(frozen=True, slots=True)
class DiscoveryPlan:
    families: tuple[str, ...] = ("beveled", "profile", "islands", "radial")
    rounds: int = 64
    batch: int = 64
    repeats: int = 3
    rays: int = 4096
    seed: int = 410000


def breed(
    values: np.ndarray,
    scores: np.ndarray,
    bounds: np.ndarray,
    rng: np.random.Generator,
    count: int,
    scale: float,
) -> np.ndarray:
    """Recombine elites, mutate normalized coordinates, reflect at box boundaries."""
    elite = values[np.argsort(scores)[-min(16, len(values)) :]]
    low, width = bounds[:, 0], bounds[:, 1] - bounds[:, 0]
    parents = (elite[rng.integers(len(elite), size=(2, count))] - low) / width
    mask = rng.random((count, len(low))) < 0.5
    children = np.where(mask, parents[0], parents[1])
    children += rng.normal(0, scale, children.shape)
    children = 1 - abs(np.mod(children, 2) - 1)
    return low + children * width


def discover(plan: DiscoveryPlan, backend: TransportBackend) -> tuple[list[Candidate], list[dict]]:
    finalists, records = [], []
    for repeat in range(plan.repeats):
        for family in plan.families:
            for method in ("random", "population"):
                rng = np.random.default_rng(plan.seed + repeat)
                all_values, all_scores = [], []
                for step in range(plan.rounds):
                    values = FAMILIES[family].sample(rng, plan.batch)
                    if method == "population" and step:
                        values[plan.batch // 4 :] = breed(
                            np.vstack(all_values),
                            np.concatenate(all_scores),
                            np.asarray(FAMILIES[family].bounds),
                            rng,
                            plan.batch - plan.batch // 4,
                            0.2 * 0.85**step + 0.025,
                        )
                    polygons = [geometry(family, x) for x in values]
                    # Two independent training seeds, common to both methods.
                    scores = np.mean(
                        [
                            measure_response(
                                polygons,
                                backend,
                                RayConfig(count=plan.rays),
                                plan.seed + 1000 + repeat * 100 + offset,
                            ).derivative
                            for offset in (0, 10)
                        ],
                        axis=0,
                    )
                    all_values.append(values)
                    all_scores.append(scores)
                    records.append(
                        dict(
                            repeat=repeat,
                            family=family,
                            method=method,
                            round=step,
                            x=values.tolist(),
                            scores=scores.tolist(),
                        )
                    )
                values, scores = np.vstack(all_values), np.concatenate(all_scores)
                best = int(np.argmax(scores))
                finalists.append(
                    Candidate(f"{family} {method} {repeat + 1}", family, tuple(values[best]))
                )
                print(f"{finalists[-1].name}: training {scores[best]:.6f}", flush=True)
    return finalists, records
