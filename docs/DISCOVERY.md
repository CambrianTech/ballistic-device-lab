# Searching beyond triangle-shaped obstacles

The triangle-heavy collection reflected a restriction in our representation:
triangles, beveled triangles, and cross-junctions were the only possibilities.
Optimizing those parameters cannot discover an unrelated topology. This experiment
expands the design space before expanding the compute budget.

## Allowed geometry

| Family | Degrees of freedom | What it can explore |
| --- | ---: | --- |
| Beveled control | 6 | Width, height, offset, tip skew, shoulder position and inset |
| Free profile | 10 | Width, height, offset, and seven independent lower-boundary depths; multiple teeth or troughs |
| Separate islands | 8 | Two independently sized and skewed triangular obstacles in disjoint left/right strips |
| Radial polygon | 12 | Elliptical envelope, center position, and eight independent radial lengths; asymmetric lobes and polygonal approximations to rounded shapes |

All share the same square cavity and four contacts. These families are broader,
but still constrained: they do not permit arbitrary pixel masks, arbitrary numbers
of holes, or movable contacts. Positive radial lengths and monotone profile knot
positions guarantee simple polygons; separated strips prevent island overlap.
Edges are straight segments, not atomically modeled boundaries or smooth curves.

## Search protocol

Four families × two methods × three repeats × 4,096 evaluations = **98,304
candidate evaluations**. Population search competes against independent global
sampling at exactly the same transport budget. Both start from the same random
first batch within each family/repeat; neither receives a hand-selected seed shape.
The previously refined bevel is an evaluation-only reference.

Population search retains the 16 strongest evaluated candidates, recombines their
coordinates, and adds Gaussian mutations in normalized parameter space. Reflected
boundaries keep proposals valid without clipping them onto parameter limits.
One quarter of every batch remains global exploration. Mutation scale decreases
from broad exploration toward a nonzero 2.5% floor. This is evolutionary population
search, not a GAN or reinforcement learning.

Training averages two fixed independent ray seeds, with 4,096 rays per input for
each seed, at mean free path/cavity width = 1 and specularity = 0.8. Fixed training
seeds provide repeatable comparisons but can still be overfit. We therefore freeze
one finalist per family/method/repeat before holdout, and retain every finalist.

The 64-round search extends a 16-round exploratory run with the same training
sequences. Its holdout uses different seeds from the exploratory run: base 820000,
four seeds, 65,536 rays per input, three mean-free-path ratios (0.5, 1, 2), and
three specularities (0.5, 0.8, 1). No holdout score enters population selection.
The exploratory run motivated a larger budget; this is not a preregistered study.

## Geometry tolerance screen

Each frozen candidate receives 16 independent parameter perturbations with a
standard deviation of 1% of its family parameter range. Samples are clipped to
the valid construction domain. Perturbed and nominal geometries use the same
32,768-ray test seed at the nominal scattering condition. Clipping can reduce
perturbations for boundary-hugging candidates; these are illustrative normalized
tolerances, not lithography specifications or calibrated manufacturing yields.

## Interpretation and stopping point

At nominal scattering, the strongest training-selected free profile scored
0.080115 on holdout, versus 0.076435 for the fixed bevel anchor (4.8% higher).
Its paired differences versus the anchor were positive on all four seeds, and
its mean exceeded the anchor under all nine scattering conditions. Its lead
over the best observed independently optimized bevel (0.079612) is much smaller;
the paired differences change sign, so the evidence does not clearly separate them.

Population search beat its matched random arm in all 12 family/repeat comparisons.
The family means across population finalists were 0.078999 (beveled), 0.074415
(profile), 0.048610 (islands), and 0.074555 (radial). A weak double-tip profile
run reduces the profile mean; reporting only the strongest shape would hide this.

The final quarter of the training budget produced no improvement in all three
radial runs and two of three beveled runs. The other beveled run gained 0.000626;
profile gains were 0, 0.000110, and 0.000602. These are optimizer plateaus under
a fixed noisy training objective, not proofs of a physical performance ceiling.

The search objective remains the angular-response derivative defined in the README.
It does not predict current, useful load power, or conversion efficiency. More
complex edges create more opportunities to exploit missing microscopic physics,
so a higher proxy score strengthens the case for a lattice check, not a device claim.

The published progress curves expose whether gains are flattening. A finite search
cannot establish a global optimum or patent novelty. Preserve diverse shapes for
quantum transport and nonlinear electrical validation, including lower-scoring
families with different path-length behavior.

## Reproduce

```sh
python validate_families.py
python -m ballistic_lab.experiments.discovery
python -m ballistic_lab.reporting.discovery runs/latest
```

Set `BALLISTIC_OUTPUT_DIR` to a fresh directory and use it in the plotting command.
The [complete snapshot](../results/2026-10-22-discovery/) includes compressed raw
training data, frozen candidates, geometry exports, validation, and tolerance results.
