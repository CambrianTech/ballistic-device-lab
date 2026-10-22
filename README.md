# Ballistic Device Lab

A simulation pipeline for discovering useful electron-transport geometries: screen many inexpensive candidates, challenge the survivors with scattering and fabrication variation, then spend detailed lattice simulation on a small, diverse shortlist.

The first target is geometry for graphene ballistic rectifiers. Our present implementation is a **classical trajectory model and geometry search**, with CPU and CUDA backends. It identifies angular steering sensitivity; it does not yet calculate electrical rectification, power efficiency, or a fabricated device's performance.

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

## License

[MIT](LICENSE). External publications remain under their respective licenses; this repository links to them rather than redistributing their text.
