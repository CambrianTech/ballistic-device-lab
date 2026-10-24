# Did early scoring hide good candidates?

Ten previously unqualified candidates were refined: the strongest and median pending candidate in each of five families. All ten passed energy and phase convergence. Maximum absolute coarse-to-refined voltage change: **0.046301 µV**. The ordering of these ten by DC power was unchanged.

| Candidate | Pending family rank | Coarse voltage (µV) | Refined voltage (µV) |
| --- | ---: | ---: | ---: |
| r0-islands-g16-0 | 42 | 1.804287 | 1.803801 |
| r0-radial-g10-1 | 1 | -7.430553 | -7.417803 |
| r0-radial-g8-1 | 43 | 1.831900 | 1.846845 |
| r0-triangle-g11-0 | 42 | 2.031900 | 2.023408 |
| r0-triangle-g12-0 | 1 | -10.743314 | -10.789615 |
| r1-beveled-g10-1 | 1 | 9.562255 | 9.553237 |
| r1-beveled-g11-0 | 41 | -2.285806 | -2.283509 |
| r1-islands-g19-1 | 1 | -9.062159 | -9.063425 |
| r1-profile-g10-0 | 41 | -2.419692 | -2.415159 |
| r1-profile-g10-1 | 1 | -8.347238 | -8.329562 |

None surpassed the completed campaign winner (12.694 µV) or synthetic control
D00 (11.205 µV). This diagnostic sample gives no evidence of large early-score
distortion among these ten. It does not establish a false-negative rate across
the full search space, validate the physical model, or prove the absence of
overlooked designs. Selection was fixed before refinement; it was not random.

The earlier allocation bug was real: unrefined did not mean failed convergence.
All ten now converged, but their scores remained close to their initial scores.
Exploration breadth and fair refinement allocation remain distinct concerns.

The audit used unchanged fixed-potential transport/scoring, copied spectra into
an isolated run, and did not alter the campaign or champion. Full before/after
records, source hashes, selection and completion receipt are included.
