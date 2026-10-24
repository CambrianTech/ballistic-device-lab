# Provisional -5 mV inner-solve audit

**Attempt outcome:** failed at 3605.85 seconds with `Charge/time budget exhausted`,
after 149 charge calls during expensive evaluation eleven. Final conditioning
was not completed. The trial output remains unresolved. A separate cold retry
uses `--max-seconds 5400` and a distinct `-seconds-5400` run directory; physics,
tolerances, the 240-charge-call cap and 24-current-evaluation cap are unchanged.
The original attempt and its lock/checkpoints are retained. The time limit is
checked between charge calls, so a call already running may finish beyond it.

Seven completed inner evaluations from the running -5 mV loaded-feedback
experiment are recorded in [audit.json](audit.json), with source-file hashes
and the worker's source manifest. The outer solve is still pending; this is
not an accepted operating point or a completed amplitude comparison.

The output-current mismatch falls from 1.692e-10 A at the initial zero-output
guess to 4.13e-17 A at evaluation four and below 6.2e-22 A for evaluations
five through seven. Those last three trial outputs are approximately
-0.995176094 microvolts. Completed inner potential residuals are about
3.71e-9 V and occupation residuals about 6.54e-10 electrons.

This shows the load iteration approaching a consistent trial point. Final
Jacobian conditioning, completion status and independent final accounting
still gate publication. Do not use this provisional output in the accepted
polarity/scaling comparison. Zero-drive offset and physical calibration are
also unresolved. This remains an uncalibrated 51-site numerical fixture.

## Runtime diagnosis at the next check-in

At 3443.96 seconds the worker had entered expensive evaluation eleven (143
charge calls). Evaluations eight and nine perturb the top output in opposite
directions; evaluation ten perturbs the bottom output. These are the final
central-difference Jacobian checks after seven root evaluations, not renewed
geometry exploration. Four extra current evaluations are needed for this check.
The worker enforces its 3600-second budget before each charge call, so a stable
root can still fail before final conditioning is available. Preserve that failure
if it occurs; a retry must explicitly budget the final checks and retain the same
physics and tolerances. Do not waive conditioning to publish the trial voltage.

Reproduce the fixed seven-evaluation projection with:

```powershell
python -m physics_layers.report_loaded_inner runs/loaded-feedback-pilot-poles-131072-cached-reverse-half audit.json --limit 7
```
