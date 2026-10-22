# Independent DC scoring audit

**No scoring discrepancy was found in these checks.** This does not validate the missing self-consistent device physics.

| Pilot finalist | Independent DC output | Difference from production |
| --- | ---: | ---: |
| D00 bevel | -11.20519 µV | 0.12408 nV |
| Fixed triangle | -3.872076 µV | 0.09195 nV |
| Mutated triangle | -5.666476 µV | 0.01585 nV |

The independent implementation uses reciprocal pair currents, eight-point Gaussian quadrature on each piecewise-linear transmission interval, and SciPy least squares for the floating output voltages. It does not call the production conductance-matrix builder, finite-bias current provider, load root or cycle-average function. Both implementations model the same fixed internal potential. The agreement tests the software under that assumption, not the assumption itself.

Additional checks:

- A closed-form, energy-linear transmission example matches both current implementations to 1e-12 relative tolerance.
- D00 rebuilt as `anonymous-reference` cannot use the archived-control shortcut; its freshly computed 257-energy score matches the cached screening score within 1 pV.
- Every archived score equals mean(Vout)² / 10 kΩ, not AC mean-square voltage or absolute mean voltage.
- Recomputing the complete screening sort reproduces the saved candidate order, including negative-polarity outputs.

The pilot's coverage was limited: eight fresh global proposals, four mutations, and no bevel-family proposals. A wider search is justified, but the scoring audit does not guarantee it will beat the incumbent.

[Machine-readable receipt and hashes](audit.json) · [Anonymous rebuilt spectrum](anonymous-reference.json.gz)

Reproduce with `python -m ballistic_lab.experiments.dc_audit` in the isolated Kwant environment, with a fresh `runs/dc-audit` directory.
