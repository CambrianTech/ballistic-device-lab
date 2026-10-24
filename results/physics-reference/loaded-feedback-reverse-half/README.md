# Completed half-amplitude polarity comparison

The cold −5 mV retry completed in 3414.38 seconds with 140 charge calls and ten expensive current evaluations. Output VB−VT is **−0.995176094 µV** into 10 kΩ. Independent KCL residual is 2.08e-21 A, power residual 6.05e-26 W and final Jacobian condition 8.82548. The previous time-limited attempt remains [preserved separately](../loaded-feedback-reverse-half-inner/README.md).

| Drive magnitude | Positive-drive output (µV) | Negative-drive output (µV) | Even component (µV) |
| --- | ---: | ---: | ---: |
| 5 mV | −0.413685102 | −0.995176094 | −0.704430598 |
| 10 mV | −2.236321536 | −3.399095170 | −2.817708353 |

Halving the drive gives an even component close to one quarter of the 10 mV value: the raw departure is −3.510 pV (about 0.0005%). This arithmetic agreement is not an accuracy estimate. Zero-drive offset has not been measured, and numerical convergence and model sensitivity remain unresolved. No uncertainty bound supports interpreting the tiny difference physically.

These are two-point operating-state diagnostics on the same uncalibrated 51-site fixture, not sinusoidal DC averages, new geometries, physical validation or novelty.

## Reproducible evidence

- [Completed solver result](result.json), [completion and source manifest](completion.json), [independent accounting](accounting.json).
- [Matched ±5 mV comparison and source-change review](polarity.json).
- [Two-amplitude diagnostic, explicitly without offset correction](scaling.json).
- [Positive half-amplitude evidence](../loaded-feedback-half/README.md) and [full-amplitude pair](../loaded-feedback-reverse/README.md).

The reviewed runner change increases only the time cap and records it in a distinct run directory. Other manifest changes are standalone reporting utilities. Physics hashes and numerical settings match across the half-amplitude pair. The retry uses a 5400-second cap; it does not reuse the failed attempt's state.
