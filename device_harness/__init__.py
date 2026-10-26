"""Physics-independent search records and distinct qualified parent selection.

Experimental API; used by the rectifier's distinct-parent adapter.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Callable, Protocol


@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    comparison_id: str
    merit: float
    qualified: bool
    evidence: str

    def __post_init__(self):
        if not all((self.candidate_id, self.comparison_id, self.evidence)):
            raise ValueError('Identity, comparison contract and evidence are required')
        if not isfinite(self.merit):
            raise ValueError('Merit must be finite; larger is better by experiment contract')


class Experiment(Protocol):
    """Adapter owns units, state dynamics, stimuli, metrics and qualification."""
    comparison_id: str

    def evaluate(self, candidate_id: str) -> Evaluation: ...

    def distance(self, left: str, right: str) -> float:
        """Symmetric normalized distance in [0, 1], under a versioned descriptor."""
        ...


def distinct_champions(records: list[Evaluation], comparison_id: str,
                       distance: Callable[[str, str], float],
                       capacity: int = 5, minimum_distance: float = .2) -> tuple[Evaluation, ...]:
    """Deterministic best-first, pairwise-separated parent archive.

    Rebuild from persisted evaluation history: insufficient diversity leaves empty
    slots. Comparison identity includes objective, solver, conditions, gates and
    distance version. No automatic cross-model ranking or physical validation.
    """
    if capacity < 1 or not isinstance(capacity, int):
        raise ValueError('Positive integer capacity required')
    if not isfinite(minimum_distance) or not 0 < minimum_distance <= 1:
        raise ValueError('Distance threshold must be in (0, 1]')
    candidates = {}
    for row in records:
        if row.comparison_id != comparison_id or not row.qualified:
            continue
        if row.candidate_id in candidates and candidates[row.candidate_id] != row:
            raise ValueError('Conflicting receipts for the same candidate')
        candidates[row.candidate_id] = row
    selected = []
    for row in sorted(candidates.values(), key=lambda r: (-r.merit, r.candidate_id)):
        distinct = True
        for member in selected:
            value = distance(row.candidate_id, member.candidate_id)
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Adapter returned invalid normalized distance')
            if value < minimum_distance:
                distinct = False
                break
        if distinct:
            selected.append(row)
            if len(selected) == capacity:
                break
    return tuple(selected)
