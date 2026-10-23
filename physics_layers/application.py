"""Application acceptance over validated stage runs, independent of search policy.

No solver is implied by a requirement. Missing evidence fails closed; numerical
acceptance is not experimental validation. Objectives belong to the campaign.
"""

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from math import isfinite
from types import MappingProxyType
from typing import Literal

from physics_layers.stages import RunIdentity, RunResult, Stage, run_stages


@dataclass(frozen=True)
class Metric:
    value: float
    unit: str

    def __post_init__(self):
        if not isfinite(self.value) or not self.unit.strip():
            raise ValueError("Finite metric and explicit unit required")


@dataclass(frozen=True)
class Metrics:
    values: Mapping[str, Metric]

    def __post_init__(self):
        values = dict(self.values)
        if not values or any(
            not name.strip() or not isinstance(value, Metric) for name, value in values.items()
        ):
            raise ValueError("Named, typed metrics required")
        object.__setattr__(self, "values", MappingProxyType(values))


@dataclass(frozen=True)
class Requirement:
    metric: str
    unit: str
    direction: Literal["minimize", "maximize"]
    limit: float

    def __post_init__(self):
        if (
            not self.metric.strip()
            or not self.unit.strip()
            or self.direction not in ("minimize", "maximize")
            or not isfinite(self.limit)
        ):
            raise ValueError("Explicit metric, unit, direction and finite limit required")


@dataclass(frozen=True)
class Application:
    name: str
    version: str
    required_stages: tuple[str, ...]
    metric_stage: str
    requirements: tuple[Requirement, ...]
    objective: str

    def __post_init__(self):
        object.__setattr__(self, "required_stages", tuple(self.required_stages))
        object.__setattr__(self, "requirements", tuple(self.requirements))
        names = [r.metric for r in self.requirements]
        if (
            not self.name.strip()
            or not self.version.strip()
            or not self.required_stages
            or any(not name.strip() for name in self.required_stages)
            or len(set(self.required_stages)) != len(self.required_stages)
            or self.metric_stage not in self.required_stages
            or len(set(names)) != len(names)
            or self.objective not in names
        ):
            raise ValueError("Versioned application, unique stages and objective required")


@dataclass(frozen=True)
class Decision:
    eligible: bool
    beats_reference: bool
    objective_value: float | None
    reference_value: float | None
    reasons: tuple[str, ...]
    application: Application
    candidate_provenance: str
    reference_provenance: str

    def manifest(self) -> dict:
        """The same decision receipt can drive selection and reporting."""
        return {"schema": "application-decision-v1", **asdict(self)}


def evaluate(identity: RunIdentity, stages: tuple[Stage, ...], app: Application) -> RunResult:
    """Preflight required evidence before spending solver time; then validate it."""
    missing = set(app.required_stages) - {stage.name for stage in stages}
    if missing:
        raise ValueError(f"Missing application stages: {sorted(missing)}")
    return run_stages(identity, stages)


def compare(candidate: RunResult, reference: RunResult, app: Application) -> Decision:
    """Apply targets and a strict improvement rule under matched model contracts.

    Source/configuration/check/assumption receipts must match. The device identity
    may differ, but materials and operating conditions must agree. No conversion
    of units, invented uncertainty margin or mixing of fidelity levels is allowed.
    """
    reasons = []
    if (
        candidate.identity.materials != reference.identity.materials
        or candidate.identity.operating_conditions != reference.identity.operating_conditions
    ):
        reasons.append("Materials or operating conditions differ")
    contracts = [{r.stage: r for r in run.receipts} for run in (candidate, reference)]
    if contracts[0] != contracts[1]:
        reasons.append("Physics source, configuration or validation contracts differ")
    for label, run, receipts in zip(("candidate", "reference"), (candidate, reference), contracts):
        missing = set(app.required_stages) - (set(receipts) & set(run.outputs))
        if missing:
            reasons.append(f"{label}: missing stages {sorted(missing)}")
    values = []
    for label, run in (("candidate", candidate), ("reference", reference)):
        metrics = run.outputs.get(app.metric_stage)
        if not isinstance(metrics, Metrics):
            reasons.append(f"{label}: missing typed metrics")
            values.append({})
            continue
        accepted = {}
        for requirement in app.requirements:
            metric = metrics.values.get(requirement.metric)
            if metric is None or metric.unit != requirement.unit:
                reasons.append(f"{label}: missing or wrong unit for {requirement.metric}")
                continue
            accepted[requirement.metric] = metric.value
            if label == "candidate":
                passed = (
                    metric.value <= requirement.limit
                    if requirement.direction == "minimize"
                    else metric.value >= requirement.limit
                )
                if not passed:
                    reasons.append(f"Target missed: {requirement.metric}")
        values.append(accepted)
    current, baseline = (value.get(app.objective) for value in values)
    eligible = not reasons
    direction = next(r.direction for r in app.requirements if r.metric == app.objective)
    beats = eligible and (current < baseline if direction == "minimize" else current > baseline)
    return Decision(
        eligible,
        beats,
        current,
        baseline,
        tuple(reasons),
        app,
        candidate.provenance_fingerprint,
        reference.provenance_fingerprint,
    )
