# Published-device comparison

The next benchmark campaign compares reconstructed published devices and searched
geometries through the same validated solver. Synthetic D00 and triangle controls
remain useful regression references, but do not substitute for a paper device.
The running campaign retains its original objective and source manifest.

## Reconstruction queue

| Reference | Available | Required before matched transport |
| --- | --- | --- |
| Auton 2016 | Scale-calibrated manual AFM contours and source pixels | Contact extensions/openings, operating conditions, boundary uncertainty family and resource estimate |
| Shi 2026 | Published SEM, constriction dimensions and material-stack record | Supplement recovery, hidden-edge parameterization, contact extensions and resolution/sensitivity treatment of dielectric thickness discrepancy |

The Auton trace is the first existing geometry to prepare for a comparison.
Shi is the newer device target. Neither currently has a matched electrical result.
Source records are in `references/auton-2016/` and `references/shi-2026/`.

## Comparison contract

1. Freeze reconstruction inputs before searching: distinguish published dimensions,
   traced boundaries and assumptions. Preserve source image hashes and dimensional
   uncertainty. Do not tune an assumed boundary to make our candidate win.
2. Establish physical scale and contact geometry. Estimate site count, memory and
   solve cost before a full-size atomistic run. A uniformly shrunk reference is a
   topology study and must never be called a physical reproduction.
3. Evaluate the reference and candidate with the same material/stack model,
   temperature, carrier-density or gate mapping, contact model, excitation and
   output load. Match numerical tolerances and convergence requirements; include
   reconstruction uncertainty and matched operating-condition sweeps.
4. First report the common-model comparison, with explicit omissions. Reproducing
   measured paper curves is a separate gate requiring compatible observables,
   device conditions and uncertainty. Frozen-potential transport alone does not
   validate the driven device physics.
5. Compare loaded DC power separately from voltage/current conversion coefficients,
   responsivity and NEP. Optical comparisons additionally require antenna coupling,
   incident/absorbed-power normalization and frequency-dependent response.
6. Publish paired curves, geometry images, convergence receipts and sensitivity
   ranges. A single operating-point win is not robust superiority. Hold out
   conditions from optimization and retain unfavorable results.

## Publication gate

Until those inputs and checks exist, the README reports **paper comparison pending**.
No paper-relative percentage or state-of-the-art claim is generated from the
synthetic-control table. Once a matched campaign completes, its reference and best
candidate become the main scientific comparison; historical synthetic-control
results remain available with their original meaning.
