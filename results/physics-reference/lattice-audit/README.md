# Fresh lattice construction audit

The saved candidate polygons were rebuilt with the production lattice constructor,
without reading cached spectra during construction or the fresh scattering solve.
This checks deterministic rebuilding; it is not an independent lattice constructor.

| Design | Sites | Connected components | Maximum transmission difference at 0.9 eV |
| --- | ---: | ---: | ---: |
| Triangle control | 7984 | 1 | 2.42e-14 |
| D00 | 7919 | 1 | 5.02e-14 |
| diversity-r0-profile-g15-1 | 6730 | 1 | 3.85e-14 |

All three have zero sites inside their etched polygons and zero shared contact
interface sites. All contacts belong to the connected device. These checks found
no disconnected-island, etch-mask or contact-overlap error. They do not exclude
narrow-neck sensitivity or certify the full energy integral/DC score.

## Reflection prerequisite

Even the empty graph has 4471 of 8723 site positions unmatched by reflection
about y=0. The chosen lattice placement and boundary cuts are not an exact
top/bottom reflection symmetry. Reflecting only the obstacle therefore changes
atomic details and is not an exact metamorphic test. A valid exact reflection
must transform lattice, boundaries and leads together; an independently rebuilt
mirrored-polygon device is instead a useful edge-sensitivity experiment.

Next checks: full-energy fresh replay, exact full-device reflection, controlled
atomic-edge perturbations, and electrostatic feedback. No physical superiority
or paper-device reproduction follows from this audit.

Run `python -m physics_layers.lattice_audit` in the isolated Kwant environment.
`results.json` retains the candidate polygons, contact component assignments and
fresh transmission/conservation diagnostics; `empty-reflection.json` records the
empty-graph symmetry prerequisite.
