"""Electrostatic kernel diagnostic at fixed geometry; no transport rerun."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
from scipy.constants import elementary_charge

from .graphene_feedback_demo import fixture
from .poisson3d import Poisson3DRequest, Poisson3DStage
from .site_mesh import SiteMeshMap


def main():
    base, mapping, equilibrium = fixture(0.0)
    matrices = []
    for factor in [1, 2]:
        shape = tuple(factor * (n - 1) + 1 for n in mapping.shape)
        spacing = tuple(h / factor for h in base.spacing_m)
        fixed = np.zeros(shape)
        fixed[1:-1, 1:-1, 1:-1] = np.nan
        faces = tuple(
            np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3)
        )
        mesh = Poisson3DRequest(spacing, faces, np.zeros(shape), fixed)
        sites = SiteMeshMap(shape, spacing, (0, 0, 0), mapping.positions_m)
        n = len(mapping.positions_m)
        kernel = np.empty((n, n))
        solver = Poisson3DStage()
        for j in range(n):
            q = np.zeros(n)
            q[j] = elementary_charge
            rho = sites.deposit_charge(q, fixed)
            assert abs(np.sum(rho) * np.prod(spacing) / elementary_charge - 1) < 1e-12
            field = solver.evaluate(replace(mesh, charge_density_c_m3=rho))
            kernel[:, j] = sites.sample_potential(field.potential_v)
        assert np.max(abs(kernel - kernel.T)) < 1e-10
        assert np.linalg.eigvalsh(kernel).min() > -1e-10
        matrices.append(kernel)
    coarse, fine = matrices
    difference = fine - coarse
    previous = Path("results/physics-reference/finite-bias-feedback/result.json")
    row = json.loads(previous.read_text())["rows"][1]
    # Same excess charge on both grids; excludes nonlinear charge redistribution.
    phi = np.array(row["potential_v"])
    reference = equilibrium.solve(np.zeros(len(phi)), [2.5, 2.5], 300, tolerance=1e-7)
    excess = np.array(row["screened"]["electrons_per_site"]) - reference.electrons_per_site
    assert np.max(abs(.03 - coarse @ excess - phi)) < 1e-8
    diagonal = np.diag(np.diag(difference))
    off = difference - diagonal
    report = dict(
        spacings_nm=[0.2, 0.1],
        kernel_v_per_positive_e=[k.tolist() for k in matrices],
        diagonal_change_range_v=[
            float(np.diag(difference).min()),
            float(np.diag(difference).max()),
        ],
        offdiagonal_max_change_v=float(np.max(abs(off))),
        frozen_charge_diagonal_potential_change_v=(-diagonal @ excess).tolist(),
        frozen_charge_offdiagonal_potential_change_v=(-off @ excess).tolist(),
        frozen_charge_total_potential_change_v=(-difference @ excess).tolist(),
        note="Fixed-charge linear decomposition, not causal attribution of the full nonlinear solution; no subtraction or renormalization applied.",
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                Path("physics_layers/site_mesh.py"),
                Path("physics_layers/poisson3d.py"),
            ]
        },
        baseline_sha256=hashlib.sha256(previous.read_bytes()).hexdigest(),
    )
    out = Path("results/physics-reference/electrostatic-kernel")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(report, indent=2))
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for k, label in zip(matrices, ["0.2 nm", "0.1 nm"]):
        axes[0].plot(np.diag(k), "o-", label=label)
    axes[0].set(xlabel="Carbon site", ylabel="On-site potential per +e (V)")
    axes[0].legend()
    for key, label in [
        ("diagonal", "On-site"),
        ("offdiagonal", "Between sites"),
        ("total", "Total"),
    ]:
        axes[1].plot(
            np.array(report[f"frozen_charge_{key}_potential_change_v"]) * 1000, "o-", label=label
        )
    axes[1].set(
        xlabel="Carbon site",
        ylabel="Fine minus coarse potential (mV)",
        title="Fixed coarse-grid charge",
    )
    axes[1].legend()
    fig.savefig(out / "kernel.png", dpi=160)
    print(
        json.dumps({k: report[k] for k in ["diagonal_change_range_v", "offdiagonal_max_change_v"]})
    )


if __name__ == "__main__":
    main()

