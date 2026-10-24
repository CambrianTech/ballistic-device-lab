# Off-resonant reference: unresolved comparison

The continuum-only charge reference rejected both attempted cases at 150 K and 600 K with `Incomplete continuum spectral weight: bound states or energy window`.

The synthetic chain uses a 0.7 eV onsite shift, reservoir chemical potentials of +0.2 and -0.1 eV, and integration over the lead band [-2, 2] eV. Unlike the previously checked unshifted chain, this case cannot be assumed to have all its local spectral weight in the continuum. The rejection prevents an incomplete reference from being treated as a trustworthy charge benchmark.

**No agreement or disagreement with the bias-charge solver was measured:** execution deliberately skipped that comparison after the reference failed. A bound-state-complete independent reference is required to resolve it. This is a verification limitation, not evidence of new physics or a defect in the bias-charge implementation. No search or loaded transport source was changed.

[result.json](result.json) preserves both rejections and source hashes. Reproduce in the Kwant environment with `python -m physics_layers.off_resonant_reference`; the output path must not already exist.
