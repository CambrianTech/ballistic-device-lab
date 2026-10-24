# Completed opposite-drive comparison

Both self-consistent loaded operating points passed root convergence, final
Jacobian conditioning, and independent current/power accounting.

| Drive | Output VB-VT | Instantaneous load power | Runtime |
| --- | ---: | ---: | ---: |
| +10 mV | -2.236321536 microvolts | 5.001134e-16 W | 3048.69 s |
| -10 mV | -3.399095170 microvolts | 1.155385e-15 W | 3026.58 s |

The two-point even component is **-2.817708353 microvolts**; the odd component
is **+0.581386817 microvolts**. Both outputs have the same sign. This is a
polarity-asymmetric response in the stated numerical fixture. It is not a
sinusoidal-cycle average, physical validation, or a novelty claim.

Reverse-drive output KCL residual is 6.27e-21 A, power residual 3.45e-26 W,
and final Jacobian condition 8.82388. It used 126 charge calls and nine
expensive evaluations, matching the positive run's counts.

[result.json](result.json), [completion.json](completion.json) and
[accounting.json](accounting.json) preserve final evidence.
[polarity.json](polarity.json) records the checked comparison and explicit
source review. Settings match; transport, charge, Poisson and fixture source
hashes match. The runner change selects drive sign and separate output paths;
other source differences are reporting modules not used in the solve.

The 51-site fixture uses uncalibrated surrogate electrodes and a chosen Gaussian
charge width and occupation closure. Before using the even response to guide
new shapes, sample intermediate drive amplitudes, establish phase convergence,
and test sensitivity to numerical and model choices. Historical fixed-potential
rankings remain separate and the old campaign stays stopped.

![Completed opposite-drive loaded outputs](polarity.png)

Reproduce this figure with `python -m physics_layers.plot_loaded_polarity`.
Only completed, accounting-checked points are plotted; no interpolated curve
or uncertainty estimate is implied. The [+5 mV run](../loaded-feedback-half/README.md)
has completed; its matching -5 mV point remains pending.
