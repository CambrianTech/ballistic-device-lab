# Four-terminal self-consistent feedback pilot

The 51-site, 0.984 nm nominal cavity uses EF 0.9 eV, 300 K, balanced 10 mV
reservoir drive, pinned output reservoirs and a 30 mV electrostatic gate.
The Gaussian charge width is 0.10 nm on a 0.10 nm mesh, dielectric constant 4.
The compensating background is the zero-onsite equilibrium occupation at EF.

Completed in 860.2 s with 60 charge calls.
Final full-grid potential residual: 2.79e-14 V;
recomputed occupation residual: 5.77e-15 electrons/site.
Potential range: 9.3591 to 12.5754 mV.

![Charge and potential](charge-potential.png)

Reservoir V means mu=EF+V and lead onsite shift=+V eV; contact electrostatic
potential is -V and device onsite shift is -phi. Remote box faces are surrogate
contacts, not a calibrated metal/graphene interface. Width, gate geometry and
bound-state occupation policy remain assumptions. This is one converged numerical
case, not a mesh study, physical validation or device-improvement claim.
Output reservoirs are pinned: these currents are not a loaded DC result.

[Result and solver source hashes](result.json) | [Completion receipt](completion.json).
Reproduce solver: `python -m physics_layers.four_terminal_feedback_pilot` (exclusive
attempt lock requires deliberate recovery before rerunning). Render completed data:
`python -m physics_layers.report_four_terminal_feedback`.
