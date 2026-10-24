# Completed +5 mV loaded feedback point

The +5 mV drive converged to output VB-VT = **-0.413685102 microvolts**
into 10 kohm. Instantaneous load power is 1.711354e-17 W.
The run took 3379.59 seconds, 140 charge calls and ten expensive current
evaluations. Final output Jacobian condition is 8.82862; independent output
KCL residual is 1.18e-22 A and power residual magnitude is 7.34e-26 W.

[result.json](result.json), [completion.json](completion.json) and
[accounting.json](accounting.json) retain the completed solver evidence and
independent accounting. The reporter requires completed status, matching source
manifests and passing circuit checks before publication.

The matching -5 mV experiment is pending. Only after both signs complete can
their even component be compared with the completed +/-10 mV pair to test
quadratic amplitude scaling. A single positive-drive point cannot establish
that scaling. Zero-drive offset, numerical convergence and model sensitivity
remain unresolved.

This is the same small 51-site numerical fixture with surrogate electrodes,
chosen Gaussian charge width and bound-state occupation closure. It is not a
sinusoidal DC average, physical validation, a new shape or a novelty claim.
