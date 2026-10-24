"""Independent analytic Gaussian-pair check of finite-width site averaging."""

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.special import erf

from .electrostatics import EPSILON_0
from .gaussian_site_mesh import GaussianSiteMeshMap


def main():
    q = 1.602176634e-19
    separation = 0.246e-9
    prefactor = q / (4 * np.pi * EPSILON_0 * 4)
    rows = []
    for sigma in (0.1e-9, 0.15e-9):
        exact = prefactor * erf(separation / (2 * sigma)) / separation
        for h in (0.1e-9, 0.05e-9, 0.025e-9):
            shape = (int(round(2e-9 / h)) + 1,) * 3
            origin = (-1e-9,) * 3
            positions = [[0, 0, 0], [0, 0, separation]]
            mapping = GaussianSiteMeshMap(shape, (h,) * 3, origin, positions, sigma)
            coordinates = np.indices(shape).transpose(1, 2, 3, 0) * h + origin
            radius = np.linalg.norm(coordinates, axis=-1)
            phi = np.full(shape, prefactor * np.sqrt(2 / np.pi) / sigma)
            np.divide(
                prefactor * erf(radius / (np.sqrt(2) * sigma)), radius, out=phi, where=radius > 0
            )
            measured = float(mapping.sample_potential(phi)[1])
            error = abs(measured / exact - 1)
            rows.append(
                dict(
                    sigma_m=sigma,
                    spacing_m=h,
                    analytic_v=exact,
                    sampled_v=measured,
                    relative_error=error,
                )
            )
        assert rows[-1]["relative_error"] < 3e-6
    out = Path("results/physics-reference/gaussian-pair")
    out.mkdir(parents=True, exist_ok=True)
    record = dict(
        separation_m=separation,
        dielectric_relative=4,
        rows=rows,
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                Path("physics_layers/gaussian_site_mesh.py"),
                Path("physics_layers/site_mesh.py"),
            ]
        },
        limitation="Analytic source potential; tests averaging only, not Poisson or graphene feedback. Chosen widths are uncalibrated.",
    )
    (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    table = "\n".join(
        f"| {r['sigma_m'] * 1e9:.2f} | {r['spacing_m'] * 1e9:.3f} | {r['sampled_v']:.8f} | {r['relative_error']:.3g} |"
        for r in rows
    )
    (out / "README.md").write_text(
        """# Gaussian pair averaging reference

Two spherical Gaussian distributions separated by 0.246 nm in dielectric 4 have
charge-averaged potential q erf(d/(2 sigma))/(4 pi epsilon d). This independent
closed form tests the mapping against an analytic source potential, without a
Poisson solve. Both widths are chosen numerical assumptions, not carbon orbital fits.
The mapping uses its default five-sigma per-axis cutoff and normalized weights.

| Width sigma (nm) | Grid (nm) | Averaged potential (V per +e source) | Relative error |
| --- | --- | --- | --- |
"""
        + table
        + """

The finest-grid error must be below 3e-6 for both widths. The residual at fine
spacing includes finite cutoff/normalization and quadrature effects; monotonic
convergence is not assumed. Width dependence remains a model uncertainty.
This checks site averaging, not the Poisson solver, finite-bias transport or
physical validity. No historical campaign or transport source is changed.

Reproduce: `python -m physics_layers.gaussian_pair_demo`.
[Machine-readable receipt](result.json).
""",
        encoding="utf-8",
    )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
