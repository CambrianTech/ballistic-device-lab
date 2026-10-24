# Provisional -5 mV inner-solve audit

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

Reproduce the fixed seven-evaluation projection with:

```powershell
python -m physics_layers.report_loaded_inner runs/loaded-feedback-pilot-poles-131072-cached-reverse-half audit.json --limit 7
```
