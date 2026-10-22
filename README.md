# Ballistic Device Lab: Searching for Better Graphene Rectifiers

**We are investigating whether optimized nanoscale geometry can improve graphene ballistic rectifiers—devices that turn an alternating electrical signal into a DC output using asymmetric electron transport.** In a ballistic device, carriers can cross the active region before bulk scattering randomizes their motion, making the shape of channels and boundaries important. Published devices already demonstrate rectification and terahertz detection; our question is whether systematic geometry search can find better candidates.

Our present implementation is a **classical trajectory model and geometry search**, with CPU and CUDA backends. We have found improved angular steering relative to our own simple control and random-search baseline. We have **not yet demonstrated electrical rectification or matched or beaten a published device**. Electrical conversion efficiency remains unknown.

The reusable framework supports this specific investigation: screen many inexpensive candidates, challenge the survivors with scattering and fabrication variation, then spend detailed graphene lattice simulation on a small, diverse shortlist.

## Where published research stands—and where we stand

These are selected experimental reference points, not an exhaustive ranking of the field. Low-frequency electrical measurements and antenna-coupled THz measurements have different input-power definitions and must not be ranked directly.

| Work | Demonstrated result | Conditions and comparison limits |
| --- | --- | --- |
| [Auton et al., 2016](https://www.nature.com/articles/ncomms11670) ([accepted manuscript](https://pure.manchester.ac.uk/ws/portalfiles/portal/33718005/CLEAN_Main_Text_Graphene_ballistic.pdf)) | Room-temperature graphene rectification; intrinsic voltage responsivity up to **23,000 V/W** and noise-equivalent power down to **0.64 pW/√Hz** | Low-frequency electrical excitation. Substrate parasitics limited measurements to 3 MHz; these sensitivity values are not a demonstrated THz result. |
| [Shi et al., 2026](https://onlinelibrary.wiley.com/doi/full/10.1002/smsc.202500654) | Antenna-coupled graphene ballistic detection at **3 THz** | Figure 3 reports sample B's maximum responsivity changing from **77 V/W at 4 K** to **6 V/W at 300 K**. The abstract separately lists 100 V/W and 20 pW/√Hz at room temperature; this apparent discrepancy needs clarification before using those headline values as a matched benchmark. |
| **This project** | Checked classical simulations, learned geometry search, finite-scattering screening, and frozen candidates | No measured device; no predicted V/W, noise-equivalent power, electrical bandwidth, or AC-to-DC power efficiency yet. Current gains are within our geometry proxy model. |

### What about efficiency?

Power-conversion efficiency is **η = useful DC power delivered to a load / AC input power**, with the input boundary specified. Detector responsivity is **DC output voltage / input power**, measured in V/W. A large output voltage into a high-impedance measurement does not by itself establish efficient power delivery.

The reference results above therefore do not give us a comparable percentage-efficiency leaderboard. Neither does our simulation: a score of 0.072 is an angular-response derivative, **not 7.2% efficiency**. To compare power efficiency, we need nonlinear voltage/current transport, a load, input coupling, and consistent power accounting. To compare detector performance, we additionally need noise and frequency response.

**Our current contribution is a reproducible candidate-discovery pipeline.** The next scientific milestone is to reproduce a published geometry's transport behavior, then evaluate our shortlist under the same physical assumptions. A state-of-the-art claim comes only after that comparison supports it.

## Why this project exists

Geometry can influence how carriers reach different terminals. We want to test whether systematic search finds useful structures beyond familiar hand-designed layouts, and eventually compare them with published devices under matched conditions. Negative results are useful: an honest ceiling can save a much more expensive simulation or experiment.

## Pipeline

| Stage | Status | Question |
| --- | --- | --- |
| Classical trajectory simulation | Implemented, CPU/GPU checked | Does the geometry steer carriers? |
| Surrogate-assisted search against random search | Implemented | Does learning improve selection at equal simulation budget? |
| Finite mean free path and small angular perturbations | Implemented | Does the response survive bulk scattering? |
| Shape perturbations and diverse shortlist | Implemented, illustrative tolerances | Which candidates deserve more detailed modeling? |
| Graphene lattice transport and edge disorder | Planned | Does the effect survive realistic electronic structure? |
| Self-consistent nonlinear transport | Planned | Does applied voltage produce useful rectification? |
| Matched literature and circuit benchmarks | Planned | Is it competitive in electrical performance, bandwidth, and noise? |

The search currently uses ExtraTrees regression and uncertainty-guided proposals with random exploration. It is active learning, not reinforcement learning. RANSAC may be useful for robust fitting of measured curves later; it is not the optimizer implemented here.

## What we have found

### New: comparing geometry families

We screened **2,304 candidates** across triangles, beveled obstacles, and asymmetric cross-junctions with equal budgets. Beveled shapes improved on the newly searched triangles in all three repeats, but **did not clearly beat our previously learned triangle**. The cross candidates had shorter long-path tails, so we retain a varied shortlist for the lattice stage.

![Frozen candidate geometry gallery](results/2026-10-22-families/families-geometries.png)

White is the conducting region, gray is excluded/etched material, and orange marks the identical contacts. The reference cross is a **literature-inspired topology approximation**, not an exact fabricated-device reconstruction.

![Fresh-seed topology comparison](results/2026-10-22-families/families-comparison.png)

Bars show the angular-response proxy; error bars are standard deviations across four fresh simulation seeds, not experimental error bars or confidence intervals. [Read the benchmark, numerical fix, limitations, and next simulation gate](docs/TOPOLOGY-BENCHMARK.md).

### Earlier search evidence

Saved evidence is in [results/2026-10-22](results/2026-10-22/). These are computational results within the stated model.

- Across three equal-budget searches, the original learned geometries averaged a 0.3541 angular steering change, versus 0.3129 for random search and 0.2266 for the simple triangle control. This uses a large imposed change in incoming angular distribution.
- Finite bulk scattering weakens the effect. At mean free path equal to the cavity width, the original learned group retains roughly half its large-perturbation response.
- A subsequent search directly targeted the infinitesimal angular response under finite scattering. On fresh seeds, its selected candidate scored **0.07213**, the random-search candidate **0.06253**, and the simple triangle **0.06013** at mean free path/cavity width = 1.
- The previously learned candidate scored **0.07276** in that same test. The new search did not establish improvement over our existing best geometry. It supports retaining a shortlist rather than declaring a new winner.

The last comparison is one search repeat, with four validation seeds and 65,536 rays per input port per seed. Scores are derivatives per dimensionless angular perturbation, **not per volt**. Neither these numbers nor the earlier scores establish superiority over published rectifiers.

![Scattering sensitivity](results/2026-10-22/rf-scattering.png)

## Model and limits

The cavity is a square of side 2 in normalized units, with four centered absorbing contacts of width 0.6. A triangular obstacle has four parameters: width, height, vertical offset, and tip skew. Boundaries mix specular and cosine-distributed diffuse reflections. Optional bulk scattering uses exponentially distributed flight lengths followed by isotropic elastic scattering.

For the small-perturbation score, s = sin(theta) has distribution p_beta(s) = [1 + beta(1 - 2s²)] / [2(1 + beta/3)]. We estimate the derivative of bottom-minus-top exit probability at beta = 0 using weights 2/3 - 2s², averaged over left and right injection. This provides a controlled geometry diagnostic without assuming an electrical voltage-to-angle law.

There is no calibrated carrier density, atomic lattice, self-consistent electrostatic potential, quantum interference, frequency response, or temperature-dependent material model yet. Static linear transmission alone does not establish DC rectification. No equilibrium thermal-noise power harvesting is claimed. Shape tolerances are illustrative, not a fabrication specification. Surrogate uncertainty is a search heuristic, not a calibrated confidence interval.

## Run

Use Python 3.12 or newer in a virtual environment:

```sh
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python simulate.py
```

GPU stages require a compatible NVIDIA GPU/driver and CuPy. The development machine used an RTX 5090 and `cupy-cuda13x[ctk]==14.2.0`; [CuPy's installation guide](https://docs.cupy.dev/en/stable/install.html) describes platform requirements. `requirements-gpu.txt` records the development environment, rather than a universal hardware requirement.

```sh
python -m pip install "cupy-cuda13x[ctk]==14.2.0"
python validate_gpu.py
python learn_search.py
python final_checks.py
python rf_screen.py
python robust_search.py
```

Run in that order: later stages consume earlier results. Outputs go to `runs/latest/`; set `BALLISTIC_OUTPUT_DIR` to a fresh directory for a new experiment. The learning search refuses to overwrite an existing learning log. Historical reports in the results snapshot retain their original prototype commands; use the commands above for this repository. GPU pool allocation is capped at 512 MiB; CUDA context/driver overhead is additional.

## Comparing against published work

The next benchmark must reconstruct published geometries and reproduce their transport trends before using the model to rank new designs. Keep dimensions, contacts, carrier density, mean free path, edge assumptions, bias, and temperature matched. Optimize controls with the same budget. Freeze candidates before evaluation, report uncertainty, and include failures.

Useful starting references:

- [Song, 1999: Formalism of nonlinear transport in mesoscopic conductors](https://journals.aps.org/prb/abstract/10.1103/PhysRevB.59.9806): nonlinear transport and geometry-dependent ballistic rectification.
- [Auton et al., 2016: Graphene ballistic nano-rectifier with very high responsivity](https://www.nature.com/articles/ncomms11670): an experimental graphene baseline.
- [Shi et al., 2026: Nanoscale Graphene-Based Ballistic Rectifiers for Detection of High Terahertz Frequency Optical Signals](https://onlinelibrary.wiley.com/doi/full/10.1002/smsc.202500654): a high-frequency detection benchmark to examine separately from low-frequency results.

Responsivity (V/W), noise-equivalent power (W/sqrt(Hz)), bandwidth, impedance, and conversion efficiency are different metrics. A geometry score cannot be substituted for any of them. We have not completed an exhaustive state-of-the-art survey or established novelty.

## Code organization and validation

The implementation is split into geometry, transport, metrics, search, validation, reporting, and experiment modules under `ballistic_lab/`. Immutable dataclass configurations and result records define interfaces; `@geometry_family` and `@validation_check` register explicit extensions. Root scripts remain short compatibility entry points. [Architecture and validation contracts](docs/ARCHITECTURE.md).

The topology search refuses to run with missing or stale source-validation receipts. CPU tests and formatting/lint checks run in CI; GPU validation additionally checks CPU agreement, reciprocity, symmetry, mixed topology batching, a grazing-boundary regression, and tolerance sensitivity. Refactoring preserved the complete recorded search output exactly.

## License

[MIT](LICENSE). External publications remain under their respective licenses; this repository links to them rather than redistributing their text.
