"""Seeded, family-balanced proposals for expensive direct-DC evaluations."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.stats import qmc

from ballistic_lab.geometry.families import FAMILIES, geometry
from ballistic_lab.search.diversity import archive


@dataclass(frozen=True, slots=True)
class WideDCPlan:
    families: tuple[str, ...] = ("triangle", "beveled", "profile", "islands", "radial")
    seeds: tuple[int, ...] = (440100, 440200)
    initial_per_family: int = 4
    feedback_rounds: int = 2
    workers: int = 4
    parent_strategy: Literal["elite", "diversity", "random"] = "elite"
    mutation_floor: float = 0.0


def proposals(plan: WideDCPlan, repeat: int, round_index: int, history: list[dict]) -> list[dict]:
    """Round zero is stratified global; later rounds pair global and mutation.

    Controls never enter the parent pool. Reflect at bounds instead of clipping
    many out-of-range mutations onto an identical parameter boundary.
    """
    result = []
    for family_index, family in enumerate(plan.families):
        seed = plan.seeds[repeat] + 1000 * round_index + 10 * family_index
        rng = np.random.default_rng(seed)
        bounds = np.array(FAMILIES[family].bounds)
        low, width = bounds[:, 0], bounds[:, 1] - bounds[:, 0]
        count = plan.initial_per_family if round_index == 0 else 1
        values = qmc.LatinHypercube(d=len(bounds), seed=seed).random(count)
        origins = ["fresh global"] * count
        if round_index:
            pool = [
                r
                for r in history
                if r["candidate"].get("repeat") == repeat and r["candidate"]["family"] == family
            ]
            elite = sorted(
                pool, key=lambda r: (-r["levels"][0]["dc_power_w"], r["candidate"]["key"])
            )[:2]
            if plan.parent_strategy == "diversity":
                elite = archive(pool)
            elif plan.parent_strategy not in ("elite", "random"):
                raise ValueError(f"Unknown parent strategy: {plan.parent_strategy}")
            parent = elite[int(rng.integers(len(elite)))]["candidate"]
            child = (np.array(parent["parameters"]) - low) / width + rng.normal(
                0, max(plan.mutation_floor, 0.16 / round_index), len(bounds)
            )
            child = 1 - abs(np.mod(child, 2) - 1)
            if plan.parent_strategy == "random":
                child = rng.random(len(bounds))
            values = np.vstack((values, child))
            origins.append(
                "fresh random"
                if plan.parent_strategy == "random"
                else f"mutation of {parent['key']}"
            )
        for index, (unit, origin) in enumerate(zip(values, origins, strict=True)):
            parameters = low + unit * width
            result.append(
                dict(
                    key=f"r{repeat}-{family}-g{round_index}-{index}",
                    family=family,
                    repeat=repeat,
                    round=round_index,
                    parameters=parameters.tolist(),
                    origin=origin,
                    obstacles=[p.tolist() for p in geometry(family, parameters)],
                )
            )
    return result
