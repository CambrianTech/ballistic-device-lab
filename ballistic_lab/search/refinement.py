"""Equal-budget global sampling versus local, feedback-guided geometry mutation."""

from dataclasses import dataclass

import numpy as np

from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.metrics.angular import measure_response
from ballistic_lab.models import Candidate, RayConfig, TransportBackend


@dataclass(frozen=True, slots=True)
class RefinementPlan:
    rounds: int = 4
    batch: int = 64
    repeats: int = 3
    rays: int = 8192
    seed: int = 170000


def proposals(
    family: str, center: np.ndarray, rng: np.random.Generator, count: int, radius: float
) -> np.ndarray:
    """Uniform sampling in a bounded local box; no clipped boundary pile-ups."""
    bounds = np.asarray(FAMILIES[family].bounds)
    width = bounds[:, 1] - bounds[:, 0]
    return rng.uniform(
        np.maximum(bounds[:, 0], center - radius * width),
        np.minimum(bounds[:, 1], center + radius * width),
        (count, len(center)),
    )


def refine(
    anchors: list[Candidate], plan: RefinementPlan, backend: TransportBackend
) -> tuple[list[Candidate], list[dict]]:
    """Both arms inherit the same anchor and spend the same new transport budget.

    The mutation arm shrinks its neighborhood after each feedback round and
    reserves a quarter of each batch for global exploration. Selection uses a
    fixed training seed within each repeat; holdout seeds live outside this API.
    """
    finalists, records = [], []
    for repeat in range(plan.repeats):
        for anchor in anchors:
            for method in ("global", "mutation"):
                rng = np.random.default_rng(plan.seed + repeat)
                center = np.asarray(anchor.parameters)
                best_score = -np.inf
                for step in range(plan.rounds):
                    if method == "global":
                        values = FAMILIES[anchor.family].sample(rng, plan.batch)
                    else:
                        local = proposals(
                            anchor.family, center, rng, plan.batch * 3 // 4, 0.2 / (step + 1)
                        )
                        global_values = FAMILIES[anchor.family].sample(rng, plan.batch - len(local))
                        values = np.vstack((local, global_values))
                    # The first evaluation includes the identical inherited anchor.
                    if step == 0:
                        values[0] = anchor.parameters
                    response = measure_response(
                        [geometry(anchor.family, x) for x in values],
                        backend,
                        RayConfig(count=plan.rays),
                        plan.seed + 1000 + repeat * 10,
                    )
                    winner = int(np.argmax(response.derivative))
                    if response.derivative[winner] > best_score:
                        best_score = float(response.derivative[winner])
                        center = values[winner].copy()
                    records.append(
                        dict(
                            repeat=repeat,
                            family=anchor.family,
                            method=method,
                            round=step,
                            x=values.tolist(),
                            scores=response.derivative.tolist(),
                            best=best_score,
                        )
                    )
                name = f"{anchor.family} {method} {repeat + 1}"
                finalists.append(Candidate(name, anchor.family, tuple(center)))
                print(f"{name}: training {best_score:.6f}", flush=True)
    return finalists, records
