"""Dependency-ordered physics runs with explicit provenance and validation gates.

This orchestrates solvers; it does not supply missing physics. A coupled
charge/transport stage owns its inner loop, including each applied bias.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class RunIdentity:
    device: str
    materials: str
    operating_conditions: str

    def __post_init__(self):
        if not all(isinstance(v, str) and v.strip() for v in self.__dict__.values()):
            raise ValueError(
                "Explicit device, material and operating-condition identities required"
            )


@dataclass(frozen=True)
class Check:
    """A named executable check. Raise on failure; returning False also fails."""

    name: str
    evaluate: Callable[[Any], bool | None]


@dataclass(frozen=True)
class Stage:
    name: str
    source_identity: str
    assumptions: tuple[str, ...]
    dependencies: tuple[str, ...]
    evaluate: Callable[[RunIdentity, Mapping[str, Any]], Any]
    checks: tuple[Check, ...]
    configuration_json: str = "{}"

    def __post_init__(self):
        configuration = json.loads(self.configuration_json)
        if not isinstance(configuration, dict):
            raise ValueError("Stage configuration must be a JSON object")
        object.__setattr__(
            self, "configuration_json", json.dumps(configuration, sort_keys=True, allow_nan=False)
        )
        for field in ("assumptions", "dependencies", "checks"):
            object.__setattr__(self, field, tuple(getattr(self, field)))
        if not self.name.strip() or not self.source_identity.strip() or not self.assumptions:
            raise ValueError("Stage name, solver source identity and assumptions required")
        if not all(isinstance(a, str) and a.strip() for a in self.assumptions):
            raise ValueError("Assumptions must be nonempty descriptions")
        names = [check.name for check in self.checks]
        if not names or any(not n.strip() for n in names) or len(set(names)) != len(names):
            raise ValueError("At least one uniquely named executable validation check required")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("Duplicate stage dependency")


@dataclass(frozen=True)
class Receipt:
    stage: str
    source_identity: str
    assumptions: tuple[str, ...]
    passed_checks: tuple[str, ...]
    dependencies: tuple[str, ...]
    configuration_json: str


@dataclass(frozen=True)
class RunResult:
    identity: RunIdentity
    outputs: Mapping[str, Any]
    receipts: tuple[Receipt, ...]

    def manifest(self) -> dict:
        """JSON-ready provenance, not a claim of experimental validation.

        Payloads stay typed and are not serialized by this layer. No result is
        reusable across runs merely because this manifest has the same hash.
        """
        return {
            "schema": "physics-stages-v1",
            "identity": dict(self.identity.__dict__),
            "stages": [dict(receipt.__dict__) for receipt in self.receipts],
        }

    @property
    def provenance_fingerprint(self) -> str:
        return sha256(json.dumps(self.manifest(), sort_keys=True).encode()).hexdigest()


class StageFailure(RuntimeError):
    def __init__(self, stage: str, completed: tuple[Receipt, ...]):
        super().__init__(f"Physics stage {stage!r} failed; downstream stages were not run")
        self.stage = stage
        self.completed = completed


def run_stages(identity: RunIdentity, stages: tuple[Stage, ...]) -> RunResult:
    """Preflight the entire graph, then run only validated upstream outputs.

    There is no global score or automatic search promotion. Validators must
    distinguish algebraic convergence, discretization error and model validity.
    Payload ownership transfers to downstream solvers, which must not mutate it.
    """
    stages = tuple(stages)
    by_name = {stage.name: stage for stage in stages}
    if not stages or len(by_name) != len(stages):
        raise ValueError("Nonempty graph with unique stage names required")
    order = []
    visiting, visited = set(), set()

    def visit(name):
        if name not in by_name:
            raise ValueError(f"Missing physics stage: {name}")
        if name in visiting:
            raise ValueError(f"Cyclic physics dependency: {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in by_name[name].dependencies:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)
        order.append(by_name[name])

    for stage in stages:
        visit(stage.name)
    outputs, receipts = {}, []
    for stage in order:
        try:
            inputs = MappingProxyType({name: outputs[name] for name in stage.dependencies})
            value = stage.evaluate(identity, inputs)
            for check in stage.checks:
                outcome = check.evaluate(value)
                if outcome is not None and outcome is not True:
                    raise ValueError(f"Validation failed: {check.name}")
        except Exception as error:
            raise StageFailure(stage.name, tuple(receipts)) from error
        outputs[stage.name] = value
        receipts.append(
            Receipt(
                stage.name,
                stage.source_identity,
                stage.assumptions,
                tuple(check.name for check in stage.checks),
                stage.dependencies,
                stage.configuration_json,
            )
        )
    return RunResult(identity, MappingProxyType(outputs), tuple(receipts))
