# Equilibrium graphene charge reference

`graphene_charge.DiracSheet` implements ideal monolayer Dirac-sheet carrier
statistics, including spin and valley degeneracy four. Temperature and Fermi
velocity are explicit inputs. The model follows the sheet statistics in
[Fang et al., Carrier Statistics and Quantum Capacitance of Graphene Sheets and
Ribbons (2007)](https://arxiv.org/abs/0707.2242).

With energies in joules inside the integral, the net electron density is

$$n-p=\frac{2}{\pi(\hbar v_F)^2}\int_0^\infty E\,[f(E-\mu)-f(E+\mu)]\,dE.$$

The public chemical-potential input is in eV; density is in m^-2. Sheet charge
relative to neutrality is minus the elementary charge times this density.
Finite-temperature integration uses the thermal correction around the exact
zero-temperature sea, with tails truncated at 50 thermal energies. The analytic
quantum capacitance supplies an independent derivative check.

`solve_planar_gate` solves a neutral sheet connected to a grounded equilibrium
reservoir beneath a uniform capacitor. The gate voltage is overdrive relative to
flat band; no unknown work-function offset is silently estimated. In this reference,
chemical potential in eV equals sheet electrostatic potential in volts:

$$C_{geo}(V_g-\phi)=e\,[n(\phi)-p(\phi)].$$

The returned charge-balance residual is in C/m². This incorporates quantum
capacitance instead of treating the sheet as a perfect metal. Tests cover the
analytic zero-temperature quadratic gate solution, electron/hole symmetry,
finite-temperature neutrality, density derivatives and series capacitance.

## Limits and next integration

This uniform, equilibrium, linear-dispersion model is a reference fixture for
electrostatics. It does not provide atom-resolved charge, edge states, finite-bias
reservoir injection, scattering or contact doping. Do not insert it into the
rectifier as a validated nonequilibrium charge closure. The live search remains
unchanged.

Next: obtain local charge from a transport model with explicit reference charge
and reservoir occupations; map sheet/site charge conservatively to the actual
dielectric stack; verify gauge consistency and converge charge and current at
every applied bias. The continuum reference helps diagnose unit/sign errors in
that integration, but cannot certify nanoscale edge physics.
