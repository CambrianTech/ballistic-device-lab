# Four-terminal graphene preflight

The new small fixture contains 51 sites including lead-attachment extensions,
with nominal cavity width 4 lattice constants (0.984 nm) and contact fraction 0.6.
The finalized system has propagating modes in all four leads: at 0.9 eV,
L/R/T/B each have one mode per spin; at 2.5 and 3.0 eV the counts are 3/3/2/2.
This permits testing near the historical 0.9 eV operating point instead of the
2.5 eV choice needed by the earlier narrow two-terminal fixture.

A 0.10 nm Poisson mesh surrounds the finalized sites with at least 0.6 nm margin.
Side-face interiors are L/R/T/B electrodes; z faces and shared side edges are
assigned to the gate explicitly. Test voltages are +5/-5/0/0 mV and gate 30 mV.
Finite-width sigma 0.10 nm site charges conserve total charge and avoid electrodes.
The uncharged Laplace field is sampled at sites in the receipt.

These remote box faces are an explicit numerical surrogate, not metal contacts
matched to the quantum lead interfaces. Contact work functions, lead-band shifts,
reservoir-voltage sign convention and bound-state reference must be chosen
consistently in the next feedback callback. No self-consistent charge, loaded DC,
rectification or device improvement is claimed by this preflight.

Reproduce: `python -m physics_layers.four_terminal_preflight` in the Kwant runtime.
[Receipt and source hashes](result.json).
