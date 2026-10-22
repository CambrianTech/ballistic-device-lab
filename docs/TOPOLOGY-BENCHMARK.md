# First topology comparison

## Result and interpretation

Three equal-budget searches per family sampled 256 candidates each: **2,304 geometry evaluations** across triangles, five-vertex beveled obstacles, and asymmetric cross-junctions. Each search selected its winner using 8,192 rays per input port. Eleven candidates, including two fixed controls, were frozen before evaluation on four new seeds, 65,536 rays per port, three mean-free-path ratios, and three wall specularities.

At mean free path/cavity width = 1 and specularity = 0.8:

| Candidate group | Mean angular-response derivative |
| --- | ---: |
| Reference cross approximation | 0.03366 |
| Optimized cross family, three winners | 0.04826 |
| Triangle family, three winners | 0.06215 |
| Beveled family, three winners | 0.06833 |
| Previously learned triangle, fixed control | 0.07385 |
| Beveled search 3, selected by its training score | 0.07368 |

The beveled family improved on the newly sampled triangle family in each repeat. It did **not** establish a meaningful advantage over the previously learned triangle. That control also stays stronger under heavier bulk scattering. Across the four nominal holdout seeds, beveled search 3 minus the prior triangle ranges from approximately -0.00052 to +0.00028.

The cross family has shorter long-path tails: nominal 99th-percentile trajectory lengths are approximately 5.6–6.9 cavity widths for its optimized candidates, versus approximately 10.6–10.9 for beveled candidates. These are trajectory diagnostics, not computed electrical bandwidths. Retaining a cross candidate can therefore be useful despite its lower angular score.

## What was reconstructed from literature

![Published device image, AFM inset and characterization: Auton et al. Figure 1](assets/literature/auton-2016-figure-1.jpg)

Figure 1 reproduced unchanged from Auton et al. (2016), [doi:10.1038/ncomms11670](https://doi.org/10.1038/ncomms11670), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The fabricated device and AFM inset are in panel (a). [Full credit and provenance](assets/literature/README.md).

We inspected the asymmetric cross topology in [Auton et al., Figure 1](https://www.nature.com/articles/ncomms11670), including the AFM image in the [accepted manuscript](https://pure.manchester.ac.uk/ws/portalfiles/portal/33718005/CLEAN_Main_Text_Graphene_ballistic.pdf). The current reference reproduces the broad topology—four terminals, narrow upper passage, wider lower passage—not the exact fabricated contour or dimensions.

All coordinates in `geometry/families.py` are **our normalized approximation**. The six reference parameters are `[0.18, 0.40, 0.06, -0.18, 0.55, 0.50]`. They are not measured dimensions extracted from the paper. Contacts are deliberately standardized to width 0.6 in a square of side 2 across all families. Real-device lead lengths, contacts, neck widths, and electrostatic conditions have not been matched.

Consequently, this is **not a reproduction of published rectification, a matched electrical benchmark, or evidence of beating state of the art**. That milestone remains open. A preferred direction under an imposed angular perturbation is insufficient to establish the paper's voltage/current law.

## Numerical validation and bug correction

The initial search stopped on a rare grazing trajectory. Diagnostic replay showed a numerical self-intersection: a reflected ray re-hit the same flat segment, crossed into the excluded obstacle, and became trapped. Both implementations now skip the previous segment until the next bulk-scattering event. The failing ray exits normally with the correction. Intersection tolerances were also reduced; changing them from 1e-10 through 1e-14 leaves all five validation geometry scores exactly unchanged in the recorded check.

The completed validation records zero destination mismatches in 65,536 deterministic CPU/GPU comparisons across four geometries and four ports. Stochastic bulk-scattering probability differences are below 0.0025 and raw reciprocity differences below 0.0033 in the tested fixtures. Mirror reversal and the zero-response empty control pass. These checks establish implementation consistency within the classical model, not validity of its material assumptions.

The source was then refactored into typed modules. A full replay produced exact equality of frozen candidates, all training scores, and all holdout statistics. Results and checks are in [the snapshot](../results/2026-10-22-families/).

## Next simulation gate

Carry the prior learned triangle, beveled search 3, cross search 1, and the unoptimized cross reference into a lattice-stage feasibility study. The first three preserve a high-response baseline, a shape variant, and a shorter-path topology; this is a deliberately varied shortlist, not a universal ranking.

Before comparing electrical metrics, resolve physical scale and lead geometry, establish a graphene tight-binding transport baseline, verify current conservation and reciprocity, and quantify discretization and edge-orientation effects. Nonlinear rectification then requires a justified voltage-dependent transport/electrostatic model. Until those steps pass, retain the angular score label and do not assign an efficiency percentage.

## Reproduce

From the repository root with the GPU environment active:

```powershell
$env:BALLISTIC_OUTPUT_DIR = 'runs/topology-reproduction'
python -m unittest discover -s tests
python validate_families.py
python compare_families.py
```

The reference control is intentionally approximate. Improving its provenance and matching physical conditions take priority over making the headline score larger.
