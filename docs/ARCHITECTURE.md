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
| `transport/quantum.py` | Optional coherent Kwant lattice stage and conservation gates |
| `transport/reservoirs.py` | Linear terminal conductance, thermal occupations, passive load and power balance |
| `experiments/linear_load.py` | Dense energy sweep and output-sensitive convergence gate; no nonlinear rectification |
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

### Physics-stage boundary

`pipeline/contracts.py` defines `PhysicsStage[Request, Result]`, separate from
the ray-only `TransportBackend`. Each solver has its own typed request and
result; a lattice solver must not fabricate ray trajectories to fit an interface.

`SquareDevice` snapshots obstacle vertices into immutable tuples, fixes the
square and centered-contact convention, and fingerprints geometry, physical
scale and `contact_width_fraction`. Identity schema v2 adds the contact fraction;
v1 hashes in historical snapshots retain their historical meaning. The ray
adapter rejects widths other than 0.3W instead of silently ignoring them.
Its optional `width_m` preserves normalized screening; physical solvers
must call `physical_width()` and reject unspecified scale. Geometry arrays handed
to solvers are copies. This contract checks dimensions and finite coordinates;
family validation remains responsible for polygon topology and nonintersection.

`pipeline/ray.py` is the first working stage adapter. `RayRequest` records ray
configuration and independent seed bases (including the second port's seed).
`RayResult` retains all per-seed observations, device identity, backend identity,
and Monte Carlo standard error. Its observable explicitly names angular response,
not power efficiency. The adapter calls the existing estimator without changing
its mathematics. It propagates solver failures instead of returning a score.
Existing search entry points retain their batched path for performance and exact
historical reproduction; the stage adapter is the boundary for staged evaluations.

Future stages receive the same device plus their own material and operating
configuration. Lattice transmission matrices, driven currents, and circuit power
budgets remain different result types. Promotion must name the observable and
comparison conditions explicitly; there is no universal cross-physics fitness.
Self-consistent electrostatics and transport belong inside one coupled stage,
with residuals and convergence failure in its result contract. Those solvers are
not implemented yet. Neither physical constants nor an assumed temperature are
silently supplied by the common device type.

The current adapter does not replace experiment-level source receipts: search
orchestration still requires the existing exact-source validation gate. Stage
results alone are not evidence of validated physics. Tests check exact estimator
parity, immutable geometry, mandatory physical scale, independent seeds, and
failure propagation before a further solver is integrated.

### Ray backend boundary

Implement `TransportBackend.trace(geometries, port, config, seed) -> TraceBatch`. The angular metric currently requires the existing uniform-contact and cosine-flux injection RNG contract. A different injection sampler requires a corresponding estimator; sharing a method signature does not make incompatible physics interchangeable.

## Required validation

- CPU-only tests check configuration rejection, polygon construction, particle conservation, an analytic angular-response case, and missing/stale validation receipts.
- GPU validation checks deterministic CPU agreement, mixed versus separate batching, stochastic bulk-scattering agreement, reciprocity, mirror reversal, the empty-cavity control, and numerical-tolerance sensitivity.
- A grazing-reflection regression pins the trajectory that formerly re-hit its own boundary and entered an excluded polygon. Reflected straight legs now exclude the previous flat segment; a bulk-scattering event clears that exclusion.
- A search requires a receipt for the exact current Python and CUDA source fingerprints. Changing source requires validation again. This is an accidental-staleness guard, not a cryptographic trust system.
- Candidates freeze before holdout evaluation. Failed or unresolved trajectories stop the run; they are never dropped from the denominator.

Run `python -m ruff check .`, `python -m ruff format --check .`, and `python -m unittest discover -s tests` locally or in CPU CI. GPU checks are run explicitly on a compatible NVIDIA machine; hosted CPU CI cannot substitute for them.

The modular refactor was replayed against the pre-refactor run: candidate parameters, every training score, and every holdout statistic were exactly equal. See the saved refactor receipt in the topology results directory.


## Quasistatic circuit interface

`transport/circuit.py` accepts a `TerminalCurrentModel`: four currents into the
L/R/T/B terminals for four applied voltages. The provider owns its transport and
self-consistency calculations and must fail if those fail. The circuit layer
solves the two output voltages with a resistor across T/B, checks terminal KCL,
local Jacobian conditioning, passivity and power balance, and integrates a
sinusoidal drive over a declared phase grid.

It reports DC voltage, DC load power, total resistor heating and ripple heating
separately. DC power is `mean(Vout)**2/R`; total heating is `mean(Vout**2)/R`.
A large AC signal therefore cannot silently become an efficiency claim. The
phase grid needs a refinement check, and the quasistatic model has no frequency
prediction or storage/filter capacitor. Models with multiple roots need branch
stability analysis; extra supplies require an extended power contract.

Independent tests cover a known resistor chain, a piecewise-linear diode bridge
with analytic output, cycle quadrature convergence, conservation failures and
floating/disconnected outputs. The bridge is a circuit oracle, not a graphene
result. The self-consistent graphene current provider remains to be implemented.

## Direct DC search and generated documentation

`search/dc_space.py` owns the seeded proposal policy and family bounds.
`experiments/dc_wide.py` evaluates those proposals through the shared finite-bias
current/circuit interfaces, freezes each batch before scoring, and refines the
automatic shortlist. Controls never enter the mutation parent pool.

`validation/dc_score.py` provides an independent numerical oracle: pair-current
integration and a different quadrature/load solver. `experiments/dc_audit.py`
also rebuilds the incumbent under an anonymous ID, checking that cached-control
handling does not change its score. This validates implementation within the
fixed-potential assumptions, not the missing electrostatic feedback.

`pipeline/dc_publish.py` accepts a completed run, archives its inputs without
overwriting a conflicting snapshot, and calls `reporting/dc_wide.py`. The
reporter applies convergence gates and ranks DC power; it generates the
finalist gallery, all-proposal plot, full table and README feature together.
There is no manually chosen hero geometry. Unresolved finalists stay visible.

`python -m ballistic_lab.pipeline.dc_workflow` runs audit → search → refinement
→ publication from fresh `runs/dc-audit` and `runs/dc-wide` directories. A
timestamped archive preserves earlier studies. `python -m
ballistic_lab.pipeline.dc_publish` publishes an already completed current run.
The workflow is a bounded explicit invocation, not a background job. Repeated
searches with unchanged seeds reproduce the same proposals; this does not
claim unbounded learning across invocations.
