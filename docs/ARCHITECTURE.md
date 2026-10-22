# Architecture and validation contracts

The research pipeline separates model definitions from experiment orchestration. New work belongs in `ballistic_lab/`; root scripts are compatibility command-line entry points.

| Module | Responsibility |
| --- | --- |
| `models.py` | Immutable dataclass configurations, candidate records, result contracts, and `TransportBackend` protocol |
| `geometry/registry.py` | `@geometry_family` registration with parameter dimensions and search bounds |
| `geometry/families.py` | Pure geometry construction; no CUDA or experiment I/O |
| `transport/cpu.py` | Independent NumPy trajectory implementation |
| `transport/gpu.py`, `rays.cu` | Batched CUDA implementation and readable kernel source |
| `transport/backend.py` | Typed adapter from low-level CUDA arrays to `TraceBatch` |
| `metrics/angular.py` | Angular-response estimator against the backend protocol |
| `search/families.py` | Equal-budget candidate generation and evaluation of frozen candidates |
| `validation/registry.py` | `@validation_check` names executable validation contracts |
| `validation/families.py` | Independent, metamorphic, regression, and tolerance checks |
| `validation/receipts.py` | Source fingerprints and rejection of missing/stale validation |
| `reporting/families.py` | Figures produced from result records; no simulation or selection |
| `experiments/` | Run orchestration and earlier reproducible experiments |

`RayConfig`, `SearchPlan`, and `Candidate` make assumptions visible at function boundaries. `TraceBatch` and `AngularResponse` name outputs that were formerly anonymous tuple positions. The geometry and validation decorators register functions without changing their callable behavior. Type annotations describe interfaces; they are not a claim that the entire project has passed a static type checker.

## Adding a geometry

Define a pure factory with `@geometry_family(name, bounds)`. Keep contacts and outer domain consistent with the intended comparison. Add tests for valid polygons and particle conservation, then CPU/GPU and physical-invariant checks before searching. A new family must not gain extra simulation budget or silently change injection conditions.

## Adding a transport backend

Implement `TransportBackend.trace(geometries, port, config, seed) -> TraceBatch`. The angular metric currently requires the existing uniform-contact and cosine-flux injection RNG contract. A different injection sampler requires a corresponding estimator; sharing a method signature does not make incompatible physics interchangeable.

## Required validation

- CPU-only tests check configuration rejection, polygon construction, particle conservation, an analytic angular-response case, and missing/stale validation receipts.
- GPU validation checks deterministic CPU agreement, mixed versus separate batching, stochastic bulk-scattering agreement, reciprocity, mirror reversal, the empty-cavity control, and numerical-tolerance sensitivity.
- A grazing-reflection regression pins the trajectory that formerly re-hit its own boundary and entered an excluded polygon. Reflected straight legs now exclude the previous flat segment; a bulk-scattering event clears that exclusion.
- A search requires a receipt for the exact current Python and CUDA source fingerprints. Changing source requires validation again. This is an accidental-staleness guard, not a cryptographic trust system.
- Candidates freeze before holdout evaluation. Failed or unresolved trajectories stop the run; they are never dropped from the denominator.

Run `python -m ruff check .`, `python -m ruff format --check .`, and `python -m unittest discover -s tests` locally or in CPU CI. GPU checks are run explicitly on a compatible NVIDIA machine; hosted CPU CI cannot substitute for them.

The modular refactor was replayed against the pre-refactor run: candidate parameters, every training score, and every holdout statistic were exactly equal. See the saved refactor receipt in the topology results directory.
