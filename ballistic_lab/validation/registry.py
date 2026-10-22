"""Named validation checks are explicit executable contracts."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    name: str
    run: Callable[[], dict]


CHECKS: list[ValidationCheck] = []


def validation_check(name: str) -> Callable[[Callable[[], dict]], Callable[[], dict]]:
    def register(function: Callable[[], dict]) -> Callable[[], dict]:
        if any(check.name == name for check in CHECKS):
            raise ValueError(f"Duplicate validation check: {name}")
        CHECKS.append(ValidationCheck(name, function))
        return function

    return register
