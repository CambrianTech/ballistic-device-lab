"""Fixed Gaussian charge: analytic-boundary Poisson convergence fixture."""

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.constants import elementary_charge, epsilon_0
from scipy.special import erf

from .poisson3d import Poisson3DRequest, Poisson3DStage


def main():
    sigma = 0.2e-9
    epsilon = 4 * epsilon_0
    charge = elementary_charge
    exact = charge / (4 * np.pi * epsilon * np.sqrt(np.pi) * sigma)
    rows = []
    for spacing in [0.2e-9, 0.1e-9, 0.05e-9]:
        axis = np.linspace(-1.2e-9, 1.2e-9, round(2.4e-9 / spacing) + 1)
        xyz = np.meshgrid(axis, axis, axis, indexing="ij")
        radius = np.sqrt(sum(x * x for x in xyz))
        shape = radius.shape
        rho = charge * np.exp(-(radius**2) / (2 * sigma**2)) / (2 * np.pi * sigma**2) ** 1.5
        analytic = np.empty(shape)
        nonzero = radius > 1e-20
        analytic[nonzero] = (
            charge
            * erf(radius[nonzero] / (np.sqrt(2) * sigma))
            / (4 * np.pi * epsilon * radius[nonzero])
        )
        analytic[~nonzero] = charge / (4 * np.pi * epsilon) * np.sqrt(2 / np.pi) / sigma
        fixed = analytic.copy()
        fixed[1:-1, 1:-1, 1:-1] = np.nan
        rho[np.isfinite(fixed)] = 0
        captured = rho.sum() * spacing**3 / charge
        assert abs(captured - 1) < 2e-6
        # Same weights for deposition and orbital-averaged sampling.
        weights = rho * spacing**3 / charge
        faces = tuple(
            np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3)
        )
        result = Poisson3DStage().evaluate(Poisson3DRequest((spacing,) * 3, faces, rho, fixed))
        averaged = float(np.sum(weights * result.potential_v))
        rows.append(
            dict(
                spacing_nm=spacing * 1e9,
                captured_charge_fraction=float(captured),
                averaged_potential_v=averaged,
                relative_error=averaged / exact - 1,
                max_potential_error_v=float(np.max(abs(result.potential_v - analytic))),
            )
        )
    assert abs(rows[-1]["relative_error"]) < 0.01
    assert all(abs(b["relative_error"]) < abs(a["relative_error"]) for a, b in zip(rows, rows[1:]))
    out = Path("results/physics-reference/finite-charge")
    out.mkdir(parents=True, exist_ok=True)
    record = dict(
        sigma_nm=0.2,
        relative_permittivity=4,
        box_side_nm=2.4,
        analytic_average_v=exact,
        boundary="Free-space Gaussian analytic Dirichlet values; tails beyond boundary negligible, not gate box",
        limitation="Chosen Gaussian test density; not a calibrated carbon pz orbital or self-interaction correction",
        rows=rows,
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__), Path("physics_layers/poisson3d.py")]
        },
    )
    (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4), layout="constrained")
    ax.plot([r["spacing_nm"] for r in rows], [100 * r["relative_error"] for r in rows], "o-")
    ax.set(
        xlabel="Grid spacing (nm)",
        ylabel="Average-potential error (%)",
        title="Fixed 0.2 nm Gaussian width: analytic reference",
    )
    ax.grid(alpha=0.3)
    fig.savefig(out / "convergence.png", dpi=160)
    print(json.dumps(record))


if __name__ == "__main__":
    main()
