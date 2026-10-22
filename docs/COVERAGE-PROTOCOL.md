# Frozen lattice coverage protocol

This protocol is written before the coverage run. It is a bounded robustness
study of linear transport, not a search for favorable operating points and not
a nonlinear rectification or state-of-the-art comparison.

## Fixed matrix

- Candidates: empty, D00 bevel, D12 profile, D14 islands, D16 radial. Frozen
  vertices come from the discovery catalog; no parameters are retuned here.
- Width: 14.76 nm. Three matched conditions per candidate: nominal contacts
  0.3W and lattice origin (0,0); wider contacts 0.4W at that origin; nominal
  contacts with lattice translated by (0.25a,0.25a). This last case samples an
  alternative atomic cut, not stochastic roughness or a crystal rotation.
- Fermi energies: 0.75, 0.90, 1.05 eV. Reservoir occupations: 300 K. Loads:
  1, 10, 100, 1000 kilohms. Differential drive: 1 mV in linear response.
- Same nearest-neighbor Hamiltonian, hopping, no lead doping, no magnetic field
  and conservation gates as the lattice checkpoint. No phonon scattering,
  electrostatic feedback, finite-frequency effects or edge passivation.

15 distinct atomic devices, 180 terminal/load observations. Each device uses
nested 257, 513 and 1025-point grids over 0.42–1.38 eV. Reuse exact prior samples
and compute only inserted energies, for 15,375 unique energy/device solves.
Two worker processes, each limited to one BLAS/OpenMP thread in this local run.
This is CPU quantum transport; the ray-search GPU is not used by this backend.

## Acceptance and reporting

Each observation must pass BOTH 257→513 and 513→1025 comparisons:
`absolute output-voltage change <= 1 nV + 1% of the finer output magnitude`.
The fixed budget ends at 1025; unresolved observations remain explicitly
unconverged. This is an empirical refinement check, not a rigorous error bound.
No output may be promoted merely because the much larger conductance entries
are stable. A failure at any energy fails that device case and stays visible.

Plots show the full candidate/condition matrix, with failed and unconverged
entries marked. Comparisons use the empty and bevel controls from the SAME
contact and atomic-cut condition. Report signed loaded voltage, not a hidden
absolute-value optimization. A sign reversal is information, not a dropped point.
Numerical grid changes are not statistical confidence intervals. The three
conditions are illustrative deterministic perturbations, not fabrication yield.

The run writes an immutable manifest with the plan, vertices and source hashes
before simulation. Per-device compressed checkpoints allow restart only under
the same manifest. Every spectrum and every refinement level is retained.
Existing historical run data are not overwritten. Resume rejects source drift.

The next study would need actual edge-disorder ensembles, additional orientations
and size scaling, followed by a specified self-consistent nonlinear model. This
matrix cannot establish universal shape rankings or useful DC power.
