"""Compatibility exports; new code imports ballistic_lab modules directly."""

from ballistic_lab.search.legacy_objective import (
    BOUNDS as BOUNDS,
)
from ballistic_lab.search.legacy_objective import (
    evaluate as evaluate,
)
from ballistic_lab.search.legacy_objective import (
    polygon as polygon,
)
from ballistic_lab.search.legacy_objective import (
    sample as sample,
)
from ballistic_lab.transport.gpu import trace_gpu as trace_gpu
