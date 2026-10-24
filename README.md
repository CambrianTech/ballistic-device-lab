# Ballistic Device Lab

<!-- activity:start -->
**Computing · Updated 2026-10-24 15:08 UTC**

Self-consistent graphene feedback · [Data snapshot](results/live/evidence.json) · Published every 15 minutes while the publisher runs.
<!-- activity:end -->

### Can the shape of graphene make a better rectifier?

We let software carve the device—and let electron transport decide which shapes work. An open computational experiment in turning an alternating electrical signal into DC, at the scale of individual carbon atoms.

![Carbon lattice of a synthetic control and a search-selected rectifier, with atomic edge closeups](results/continuous-dc/round-000430/atomic-comparison.png)

**Same material. Same drive. Different geometry.** The selected shape produces **28.33 µV** versus **11.21 µV** for the synthetic control in the fixed-potential simulation. Bright dots are carbon sites; black openings are etched voids. These are simulated lattices, not microscope images.

[Explore the shapes](#letting-shapes-compete) · [Follow the electrons](#following-the-electrons) · [Look inside the physics](#the-charge-changes-the-device) · [Run the code](#reproduce-and-explore)

## Letting shapes compete

A triangle is only the beginning. The search explores bevels, free profiles, islands and radial polygons, testing how each changes the output across a four-contact graphene device. Input runs left to right; the load connects top to bottom.

![Five geometry families and the synthetic control, with convergence labels](results/continuous-dc/round-000430/diversity.png)

*Colored polygons are removed material; white space conducts. Orange marks the contacts. Screening-only candidates remain visibly distinct from numerically converged results.*

Three strategies start with the same population: mutate the strongest designs, preserve different kinds of shapes, or sample randomly. Each candidate passes through transport, load solving and numerical refinement before it can become a converged winner.

```mermaid
flowchart LR
    A[Propose a shape] --> B[Solve electron transport]
    B --> C[Measure DC load power]
    C --> D[Check convergence]
    D --> E[Select and diversify]
    E --> A
```

![Best converged output as the three search strategies explore successive rounds](results/continuous-dc/round-000430/progress.png)

**430 matched rounds · 8,640 candidates per strategy · five shape families.** Published snapshots keep the figures, candidate identities and evidence together. Equal candidate counts do not imply equal CPU time or prove one algorithm superior.

<details>
<summary><strong>Compare the converged results</strong></summary>

| Selection method | DC magnitude (µV) | DC load power (pW) |
| --- | ---: | ---: |
| Synthetic control D00 | 11.205 | 0.01256 |
| Top-score selection | 27.150 | 0.07371 |
| Diversity archive | 28.331 | 0.08026 |
| Random search | 22.319 | 0.04981 |

Matched conditions: 14.76 nm device width, 10 mV peak sinusoidal drive, 10 kΩ load, 300 K and fixed internal potential. DC power excludes ripple heating. D00 and triangle-control are synthetic references.

[Full results and candidate identities](results/continuous-dc/round-000430/README.md) · [Independent scoring audit](results/2026-10-22-dc-audit/README.md)

</details>

<!-- evolution:start -->
**Champion to beat: 28.331 µV DC.** Latest completed generation: **432**. The champion survives restarts; records from different source manifests remain separate.

![Parents and latest diverse attempts](results/live/generation.png)

The strip selects new attempts by screening score within each family, not by visual preference. Parent links come from recorded mutation origins; fresh samples have no parent. [Selection evidence](results/live/evidence.json) · [Champion ledger](results/live/champions.json).
<!-- evolution:end -->

## Following the electrons

The geometry gives electrons different routes through the device. Trajectory diagrams make that routing visible; the quantum calculation determines the electrical score.

![Classical electron trajectories through the control and selected shapes](results/continuous-dc/round-000430/leader-trajectories.png)

*Classical trajectories illustrate steering under matched injection. They are a separate diagnostic, not quantum paths or a direct measurement of rectification.*

A strong score at one operating point is only part of the story. The nominal winner beats D00 in **13 of 27** tested conditions; its median power ratio is **0.445×**. Changing contacts or operating conditions can reverse the ranking.

<details>
<summary><strong>Explore scattering, contacts and atomic edges</strong></summary>

### Scattering changes the routes

![Matched classical scattering comparison](results/continuous-dc/round-000430/leader-scattering.png)

### Contacts and energy change the ranking

![Contact and Fermi-energy sensitivity](results/continuous-dc/round-000430/leader-coverage.png)

![Validation matrix with completed and unresolved cases](results/continuous-dc/round-000430/leader-matrix.png)

### Small edge changes make distinct devices

![Simulated atomic lattice and local edge mutations](results/continuous-dc/round-000430/winner-local/atomic-lattice.png)

[Robustness evidence](results/continuous-dc/round-000430/robustness) · [Local mutations](local_lab/README.md) · [Atomic-vacancy experiments](edge_lab/README.md)

</details>

## The charge changes the device

Geometry is only one part of the physics. Electrons redistribute charge, charge changes the electrostatic potential, and that potential changes transport. A separate self-consistent graphene–Poisson experiment resolves that feedback at individual lattice sites.

![Site-resolved self-consistent potential and excess charge in a four-terminal graphene fixture](results/physics-reference/four-terminal-feedback/charge-potential.png)

*Potential and excess charge on a 51-site numerical fixture with pinned outputs. This experiment is distinct from the fixed-potential geometry rankings above.*

With a load connected, opposite drives produce unequal outputs. At ±10 mV the two-point even component is **−2.818 µV**; at ±5 mV it is **−0.704 µV**, close to one quarter. That is consistent with quadratic scaling in this diagnostic, while zero-drive offset and numerical sensitivity remain unresolved.

<details>
<summary><strong>Inspect the loaded response and model assumptions</strong></summary>

<!-- loaded-points:start -->
| Drive (mV) | Output (µV) | Evidence |
| ---: | ---: | --- |
| -10 | -3.399095 | `loaded-feedback-pilot-poles-131072-cached-reverse` |
| -5 | -0.995176 | `loaded-feedback-pilot-poles-131072-cached-reverse-half-seconds-5400` |
| 5 | -0.413685 | `loaded-feedback-pilot-poles-131072-cached-half` |
| 10 | -2.236322 | `loaded-feedback-pilot-poles-131072-cached` |

Individual operating points; source manifests and accounting are retained in the [data snapshot](results/live/evidence.json).
<!-- loaded-points:end -->

![Completed loaded-feedback operating points](results/live/loaded-points.png)

These are individual operating points, not a sinusoidal DC average. The fixture uses surrogate contacts, a chosen Gaussian charge width and an explicit bound-state occupation rule. Numerical checks verify calculations within these assumptions; they do not establish fabricated-device performance or literature novelty.

[Matched amplitude comparison](results/physics-reference/loaded-feedback-reverse-half/README.md) · [Charge and feedback experiments](physics_layers/FINITE_BIAS.md) · [Model qualification](docs/DEVICE-ROLE.md)

</details>

## Reproduce and explore

The repository includes geometry generation, coherent quantum transport, circuit solving, charge/Poisson experiments and reproducible reports. Quantum calculations use **Kwant**; optional GPU trajectory studies use **CUDA**.

```sh
# In an environment with the repository dependencies installed:
python -m unittest discover -s tests

# Render completed search snapshots:
python -m ballistic_lab.reporting.dc_continuous
```

[Run your own continuously published fork](docs/PUBLICATION.md) · [Python dependencies](requirements.txt) · [Quantum environment](environment-quantum.yml) · [GPU dependencies](requirements-gpu.txt) · [Worker and source-manifest contracts](docs/ARCHITECTURE.md)

| Explore | Read |
| --- | --- |
| Experiments and diagrams | [Evidence index](docs/EVIDENCE-INDEX.md) · [Detailed experiment record](docs/EXPERIMENT-RECORD.md) |
| Detector sensitivity | [Noise audit](results/physics-reference/detector-audit/README.md) · [Conventional reference](references/conventional-detectors/README.md) |
| Published devices | [Auton et al.](references/auton-2016/README.md) · [Shi et al.](references/shi-2026/README.md) · [Matched comparison criteria](docs/PAPER-COMPARISON.md) |

**Research software.** The application is sensitive signal detection; no design is qualified against a fabricated or commercial detector. Real contacts, driven noise, fabrication yield and finite-frequency response require separate evidence.

## Future experiments

**Neuromorphic devices:** use the same propose–simulate–test loop to explore geometries and circuits with useful memory and neuron-like dynamics. Those experiments will measure time-dependent state, switching energy and robustness against matched controls. Static rectification alone does not demonstrate neuromorphic behavior.

[MIT license](LICENSE). External figures retain their stated licenses.
