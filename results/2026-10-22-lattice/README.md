# Graphene lattice transport checkpoint

The pipeline now solves a coherent graphene tight-binding transport problem,
using Kwant 1.5.0. This is a first lattice checkpoint, not a device-performance
claim. Raw reference checks and every transmission matrix are in `lattice.json`.

## Model

- Nearest-neighbor honeycomb lattice; one orbital per site, one spin species.
  Conventional model parameters: lattice constant 0.246 nm, hopping 2.7 eV.
  These are declared assumptions, not fitted parameters for a fabricated stack.
- Square active region, nominal widths 40 and 60 lattice constants (9.84 and
  14.76 nm); four centered contacts with nominal width 0.3W.
- Primitive vectors `(1,0)` and `(1/2,sqrt(3)/2)`, basis `(0,0)` and
  `(0,1/sqrt(3))`; lead translations `(-1,0)`, `(1,0)`, `(-1,2)`, `(1,-2)`.
- Atom removal implements obstacle boundaries. No passivation, reconstruction,
  edge disorder, strain, magnetic field, spin-orbit coupling, phonons or dephasing.
  The discrete cut determines actual edge termination and contact width; the
  atomically cut device need not retain the continuum shape's mirror symmetry.
  Kwant may add interface sites when attaching periodic leads.
- Uniform zero onsite energy, identical undoped leads. Nine electron energies
  from 0.15 to 1.35 eV, spacing 0.15 eV; no thermal occupation integration.
- Frozen shortlist: D00 beveled anchor, D12 profile, D14 separated islands,
  D16 radial polygon, plus empty control. This is not a quantum-optimized search.
- 3,169–8,723 sites in the four-terminal systems. These small test devices do not
  reproduce the dimensions or contact physics of a published rectifier.

## Validation and what it teaches

At both widths a matched, obstacle-free two-terminal ribbon transmits its full
incoming mode count at every sampled energy. Hamiltonian Hermiticity, scattering
unitarity, conservation, zero-field reciprocity and equal-occupation cancellation
are checked before accepting data. The largest four-terminal residual is
**3.50e-12** (acceptance tolerance 1e-7). Shifting ribbon onsite energies and probe
energies together by 0.137 eV changes transmission by at most **5.74e-13**.
This is a uniform energy-reference test, not a nonlinear electrostatic solver test.

For the 9.84 nm device, left/right contacts have zero propagating modes at sampled
energies 0.15–0.60 eV; the first sampled conducting point is 0.75 eV. At 14.76 nm
they conduct at every sampled energy. These cutoffs are consequences of this
particular atomic lead construction, not a universal graphene threshold.

![Transmission and lead modes](lattice-transmission.png)

The plotted imbalance is `(T_bottom,left - T_top,left)/N_left`; missing points
mean no incoming left mode. It is not the ray angular derivative, output voltage,
or conversion efficiency. Empty-cavity imbalance is retained visibly: contacts
and discrete edges already contribute directional structure. Lines only guide
the eye across sparse samples; step locations are not exact band edges.

**Conclusion:** directional transport depends strongly on energy, width and
contacts. No single winner is established. Broader energy sampling, different
atomic cuts/orientations, contact engineering and size studies are needed before
ranking candidates. Two different physical widths are not mesh convergence:
the carbon lattice spacing is fixed. Next, driven charge transport requires a
self-consistent electrostatic model, then reservoir/load equations and power
accounting. Static transmission does not establish rectification.

## Reproduce

Create a separate environment with `conda env create -f environment-quantum.yml`,
then `conda activate ballistic-quantum`. From the repository root:

```text
python -m unittest discover -s tests -p test_quantum.py
python -m ballistic_lab.experiments.lattice
```

The experiment refuses to overwrite `runs/lattice/lattice.json`. Rendering uses
`python -m ballistic_lab.reporting.lattice` against this published snapshot.
Ordinary CPU CI skips the two Kwant integration tests when Kwant is absent;
both were run successfully in the isolated environment on Windows. The solver
uses CPU sparse linear algebra, not CUDA. Local micromamba's run wrapper failed
silently on a later invocation; direct environment Python with its `Library/bin`
on PATH completed the run. No solver failures were discarded or converted to zeros.

Sources: [Kwant graphene tutorial](https://kwant-project.org/doc/latest/tutorial/graphene),
[Kwant transport paper](https://arxiv.org/abs/1309.2926).
