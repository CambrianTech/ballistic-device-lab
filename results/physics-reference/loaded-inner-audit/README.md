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

## Provisional operating point after seven inner solves

The seventh completed evaluation has output VB-VT = **-2.23632 microvolts**
at a single +10 mV drive and a 10 kohm load. The maximum output KCL residual
is **2.44e-21 A**, down from 3.49e-10 A initially. Final inner potential
and occupation residuals are 4.38e-9 V and 6.95e-10 electrons/site.

Independent bookkeeping from the recorded currents and voltages gives:

| Quantity | Value |
| --- | ---: |
| Input power | 2.7371326444e-9 W |
| Device absorption | 2.7371321443e-9 W |
| Load power | 5.0011340e-16 W |
| Input minus device minus load | -2.37e-26 W |

The power residual agrees with minus the output-voltage-weighted KCL
residual to floating-point precision; device absorption is positive.
These checks support this operating point but do not replace the outer
solver's remaining Jacobian-conditioning checks. The worker is still running.
This instantaneous load power is **not rectified DC power**; reverse drive
and an AC cycle have not been evaluated with this model.

[first-seven.json](first-seven.json) preserves this expanded compact audit;
the earlier five-record snapshot remains unchanged. Reproduce using the same
report command with `first-seven.json --limit 7`. No live solver source changed.

## Bounded attempt outcome

The attempt stopped after **3611.98 seconds**, at 147 charge calls and
11 circuit callbacks, with `Charge/time budget exhausted`. The one-hour
limit is checked between charge calls, so an in-flight call can finish after
3600 seconds. Ten completed inner evaluations remain preserved locally.
[Final status and source manifest](budget-stop.json).

The seventh point's KCL and power audit remains valid, but the complete outer
conditioning check did not finish. No final loaded result or DC result is claimed.

Before a new attempt, the exact-voltage cache was tested through the complete
load solver against independent passive resistor and diode-bridge fixtures at
both drive signs. It reduced provider calls from 13 to 10 (resistor) and
12 to 9 (bridge), with identical complete solution records including Jacobian
conditioning, currents and power. The sets of distinct evaluated voltages also
match exactly. Six cache/circuit tests passed. These are software verification
fixtures, not graphene performance measurements; actual runtime savings remain
unmeasured. The next bounded attempt can integrate the cache in a fresh run
folder while preserving this failed attempt and its evidence.
