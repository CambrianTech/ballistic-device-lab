# Fresh-campaign benchmark inputs

`benchmarks.json` retains the synthetic D00 control and converged champion
geometries at their 14.76 nm width and 0.3 contact fraction. Their new-model
scores are deliberately null until matched evaluation completes. The 51-site
integration replay is a different, much smaller fixture; its scores cannot be
compared with these benchmarks.

Fork users can freeze their own retained records:

```sh
python -m ballistic_lab.pipeline.prepare_feedback_campaign --ledger results/live/champions.json --controls results/2026-10-22-dc-wide/summary.json --width-m 1.476e-8 --contact-fraction 0.3 --output runs/my-new-campaign/benchmarks.json
```

The output must be new. Explicit dimensions prevent silent rescaling, and source
hashes preserve input provenance. The tool neither deletes the ledger nor starts
compute workers. Changed models require new evaluation of retained designs.

Launch gates: geometry-adapter numerical replay; bounded feasibility at benchmark
scale; matched control/champion load solves; energy/phase refinement and model
sensitivity. A smaller exploratory device scale must be a separately labeled
experiment, not a claimed improvement over this champion. The old STOP remains.

## Capacity at the retained physical scale

The lattice-only preflight in `capacity.json` counts the actual retained geometries:

| Benchmark | Atomic sites | Storage for one dense complex128 matrix |
| --- | ---: | ---: |
| D00 synthetic control | 7,919 | 1.003 GB |
| Retained champion | 6,715 | 0.721 GB |

The charge reference backend constructs dense matrices and performs repeated
matrix inversions. These counts expose a scalability barrier before launching a
population search with charge feedback. Matrix storage is only a lower bound;
the recorded cubic work ratios are asymptotic comparisons with the 51-site
fixture, **not measured timings or runtime forecasts**. This check does not solve
charge, Poisson feedback or transport, and establishes no device performance.

Reproduce against any fork's frozen benchmark set (output must not exist):

```sh
python -m ballistic_lab.pipeline.feedback_capacity runs/my-new-campaign/benchmarks.json runs/my-new-campaign/capacity.json
```

Full-scale feedback search remains gated on demonstrated computational feasibility.
The retained champion stays intact. A small-device experiment would have its own
baseline and champion rather than inheriting the full-scale performance claim.
