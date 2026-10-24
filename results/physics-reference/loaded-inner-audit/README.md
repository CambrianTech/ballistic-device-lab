# Loaded-feedback inner evaluation audit

This snapshot preserves the first five completed inner solves from the
131072-pole-budget loaded pilot. The outer circuit solve remains unresolved;
these are not a loaded output result, rectified DC, or physical validation.

The first three calls repeat exactly the same reservoir voltages:
[+5, -5, 0, 0] mV. The next two perturb one output by
1.4901161193847657e-10 V for the outer solver's numerical Jacobian.
All five pass the inner charge/potential checks. At the unperturbed point,
the output KCL residuals are -0.3490 and -0.1209 nA. Thus converged
charge feedback alone does not solve the external load constraint.
Total terminal current sums have magnitude below 8.1e-23 A.

Three identical calls also confirm a concrete optimization opportunity:
the separately tested exact-voltage cache can avoid two full repeated solves
in a future run. It is not installed in this live attempt. Tiny distinct
Jacobian voltages must retain their own evaluations.

[first-five.json](first-five.json) contains currents, reservoir voltages,
final inner residuals, recalculated 10 kohm output KCL residuals, each raw
record's SHA-256, and the worker's source manifest. Full meshes remain in the
local run checkpoint; this compact projection avoids duplicating them.

Reproduce from the preserved run with:

```powershell
python -m physics_layers.report_loaded_inner runs/loaded-feedback-pilot-poles-131072 results/physics-reference/loaded-inner-audit/first-five.json --limit 5
```

Assumptions remain those of the 51-site fixture: chosen charge width,
surrogate electrodes, and explicit reference occupation closure. Final load,
power-accounting and AC-cycle checks are still required.
