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
