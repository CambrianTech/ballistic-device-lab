# Four-terminal finite-bias charge benchmark

The 51-site fixture now evaluates finite-bias charge at 300 K with reservoir
chemical potentials [0.905, 0.895, 0.900, 0.900] eV in L/R/T/B order. All device
onsite and lead-band shifts are zero. Bound occupations use reference 0.900 eV.
This isolates the charge backend before coupled electrostatics and circuit loading.

Tightening requested tolerance from 1e-6 to 1e-7 changes occupation by at most
3.10e-9 electrons/site and terminal current by 2.12e-21 A. Evaluations took
12.44 and 18.42 seconds on this host with single-thread BLAS. Input current is
about 0.271 microampere; output-terminal currents are nonzero with their chemical
potentials pinned, so these are not floating/load-solved voltages or DC power.
The provider's terminal-current conservation check passed for both evaluations.

Two tolerances check integration sensitivity at one fixed Hamiltonian, not physical
validation, orbital/contact calibration, mesh convergence or rectification. A full
load evaluation needs repeated self-consistent solves: this cost is a reason to
measure and reuse voltage-independent Poisson operators before launching a search.
No stale charge solution or frozen spectrum may replace a failed feedback solve.

Reproduce: `python -m physics_layers.four_terminal_charge` in the isolated Kwant
runtime with single-thread BLAS. [Receipt and source hashes](result.json).
