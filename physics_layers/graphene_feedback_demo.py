"""Small equilibrium graphene/gate-box verification, not a rectifier prediction."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system

from .equilibrium_charge import EquilibriumChargeDevice
from .poisson3d import Poisson3DRequest
from .site_acceleration import solve_accelerated
from .site_mesh import SiteMeshMap


def fixture(gate_v=0.03):
    system = build_system(SquareDevice((), 2 * 0.246e-9), LatticeRequest((0.7,)), ribbon=True)
    xy = np.array([site.pos for site in system.sites]) * 0.246e-9
    spacing = (0.2e-9,) * 3
    positions = np.c_[np.zeros(len(xy)), xy[:, 1], xy[:, 0]]
    positions -= positions.min(axis=0)
    positions += 3 * spacing[0]
    shape = tuple((np.ceil(positions.max(axis=0) / spacing[0]).astype(int) + 4).tolist())
    fixed = np.full(shape, gate_v)
    fixed[1:-1, 1:-1, 1:-1] = np.nan
    faces = tuple(np.full(tuple(n - (a == i) for i, n in enumerate(shape)), 4.0) for a in range(3))
    mesh = Poisson3DRequest(spacing, faces, np.zeros(shape), fixed)
    mapping = SiteMeshMap(shape, spacing, (0, 0, 0), positions)
    return mesh, mapping, EquilibriumChargeDevice(system)


def main():
    mesh, mapping, provider = fixture()
    result = solve_accelerated(
        mesh, mapping, provider, np.ones(len(mapping.positions_m)), [0, 0], 300, tolerance=1e-5
    )
    out = Path("results/physics-reference/graphene-feedback")
    out.mkdir(parents=True, exist_ok=True)
    record = dict(
        source_sha256={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path("physics_layers/graphene_feedback_demo.py"),
                Path("physics_layers/equilibrium_charge.py"),
                Path("physics_layers/site_acceleration.py"),
                Path("physics_layers/site_mesh.py"),
                Path("physics_layers/poisson3d.py"),
            ]
        },
        model="Equilibrium nearest-neighbor graphene, ideal leads, dielectric gate box",
        limitations="15-site verification fixture; no finite-bias rectification, calibrated stack, exchange or phonons",
        gate_v=0.03,
        temperature_k=300,
        dielectric_relative=4,
        spacing_m=mesh.spacing_m,
        positions_m=mapping.positions_m.tolist(),
        plan={"method": "Hybrid root in site space", "tolerance": 1e-5},
        site_potential_v=result.site_potential_v,
        excess_charge_c=result.excess_charge_c,
        transport=asdict(result.transport),
        history=[asdict(x) for x in result.history],
    )
    (out / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), layout="constrained")
    xy = mapping.positions_m[:, [2, 1]] * 1e9
    for ax, values, label in zip(
        axes[:2],
        [
            np.array(result.site_potential_v) * 1000,
            np.array(result.transport.electrons_per_site) - 1,
        ],
        ["Screened potential (mV)", "Excess electrons per carbon"],
    ):
        dots = ax.scatter(*xy.T, c=values, cmap="viridis", s=100, edgecolors="black")
        fig.colorbar(dots, ax=ax, label=label)
        ax.set(xlabel="x (nm)", ylabel="y (nm)", aspect="equal")
    axes[2].semilogy(
        [s.potential_residual_v for s in result.history], label="Potential residual (V)"
    )
    axes[2].scatter(
        [len(result.history) - 1],
        [result.history[-1].occupation_residual],
        label="Final occupation residual",
        color="tab:orange",
    )
    axes[2].set(xlabel="Residual evaluation", title="Unmixed feedback residuals")
    axes[2].legend(fontsize=8)
    fig.suptitle("Equilibrium graphene screening | 30 mV gate-box fixture | 300 K")
    fig.savefig(out / "screening.png", dpi=180)
    print(
        json.dumps(
            dict(
                residual_evaluations=len(result.history),
                potential_range_v=[min(result.site_potential_v), max(result.site_potential_v)],
                last=asdict(result.history[-1]),
            )
        )
    )


if __name__ == "__main__":
    main()
