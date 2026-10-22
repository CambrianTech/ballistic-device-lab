"""Rebuild field illustrations and analytic mesh-convergence evidence."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .electrostatics import EPSILON_0
from .poisson3d import Poisson3DRequest, Poisson3DStage, deposit_sheet


def face_maps(shape, epsilon=4.0):
    return tuple(
        np.full(tuple(n - (a == axis) for a, n in enumerate(shape)), epsilon) for axis in range(3)
    )


def boundary(exact):
    fixed = exact.copy()
    fixed[1:-1, 1:-1, 1:-1] = np.nan
    return fixed


def main():
    destination = Path("results/physics-reference/electrostatics-3d")
    destination.mkdir(parents=True, exist_ok=True)
    n = 25
    h = 2e-9
    axis = (np.arange(n) - n // 2) * h
    yy, xx = np.meshgrid(axis, axis, indexing="ij")
    fixed = boundary(np.zeros((n, n, n)))
    sigma = np.where((abs(xx) <= 10e-9) & (abs(yy) <= 10e-9), 1e-4, 0)
    rho = deposit_sheet(sigma, n // 2, (h, h, h), fixed)
    result = Poisson3DStage().evaluate(
        Poisson3DRequest((h, h, h), face_maps(fixed.shape), rho, fixed)
    )
    records = []
    for count in (7, 11, 17, 25):
        z, y, x = np.meshgrid(*(np.linspace(0, 1, count) for _ in range(3)), indexing="ij")
        exact = np.sin(np.pi * z) * np.sin(np.pi * y) * np.sin(np.pi * x)
        lengths = np.array([20e-9, 30e-9, 50e-9])
        charge = 4 * EPSILON_0 * np.pi**2 * np.sum(1 / lengths**2) * exact
        electrodes = boundary(exact)
        charge[np.isfinite(electrodes)] = 0
        solved = Poisson3DStage().evaluate(
            Poisson3DRequest(
                tuple(lengths / (count - 1)), face_maps(exact.shape), charge, electrodes
            )
        )
        records.append(
            {
                "nodes_per_axis": count,
                "relative_step": 1 / (count - 1),
                "max_error_v": float(np.max(abs(solved.potential_v - exact))),
                "residual_c_m3": solved.residual_c_m3,
            }
        )
    np.savez_compressed(
        destination / "fields.npz",
        axis_m=axis,
        sigma_c_m2=sigma,
        potential_v=result.potential_v,
        rho_c_m3=rho,
    )
    receipt = {
        "model": "prescribed finite sheet; grounded box; uniform relative permittivity 4; no transport feedback",
        "spacing_m": h,
        "sheet_density_c_m2": 1e-4,
        "total_charge_c": float(rho.sum() * h**3),
        "convergence": records,
        "sources": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                Path(__file__),
                Path(__file__).with_name("poisson3d.py"),
                Path(__file__).with_name("electrostatics.py"),
            )
        },
    }
    receipt["sources"] = {Path(k).name: v for k, v in receipt["sources"].items()}
    (destination / "results.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3), layout="constrained")
    extent = (axis[0] * 1e9, axis[-1] * 1e9, axis[0] * 1e9, axis[-1] * 1e9)
    for ax, data, title, ylabel in (
        (axes[0], result.potential_v[n // 2], "Potential in the charged-sheet plane", "y (nm)"),
        (
            axes[1],
            result.potential_v[:, n // 2, :],
            "Field spreads above and below the sheet",
            "z (nm)",
        ),
    ):
        im = ax.imshow(data * 1e3, origin="lower", extent=extent, cmap="magma")
        ax.set(title=title, xlabel="x (nm)", ylabel=ylabel)
        fig.colorbar(im, ax=ax, label="Potential (mV)", shrink=0.8)
    steps = np.array([r["relative_step"] for r in records])
    errors = np.array([r["max_error_v"] for r in records])
    axes[2].loglog(steps, errors, "o-", color="#087f8c", label="3D solver")
    axes[2].loglog(
        steps,
        errors[-1] * (steps / steps[-1]) ** 2,
        "--",
        color="#d68b30",
        label="Second-order reference",
    )
    axes[2].set(
        title="Independent analytic accuracy check",
        xlabel="Normalized mesh spacing",
        ylabel="Maximum potential error (V)",
    )
    axes[2].legend()
    axes[2].grid(alpha=0.2)
    fig.suptitle(
        "3D electrostatics building block · prescribed charge, not a device prediction", fontsize=14
    )
    fig.savefig(destination / "fields-and-convergence.png", dpi=170)
    plt.close(fig)
    (destination / "README.md").write_text(
        "# 3D electrostatics verification\n\n![Fields and convergence](fields-and-convergence.png)\n\nLeft: potential of a prescribed positive square sheet patch. Center: vertical cross-section showing fringing. All six box faces are grounded; relative permittivity is 4, spacing is 2 nm, sheet density is 0.1 mC/m². Finite box size affects this illustration. Right: a separate manufactured sine solution on an unequal-spacing 3D mesh converges at second order.\n\nThis verifies a field building block, not graphene transport or a winning design. The actual dielectric/contact stack, atomistic charge mapping, reference charge and self-consistent transport closure remain pending. Rebuild with `python -m physics_layers.electrostatic_demo`. Raw fields, convergence values and source hashes are stored alongside this image.\n",
        encoding="utf-8",
    )
    print(destination)


if __name__ == "__main__":
    main()
