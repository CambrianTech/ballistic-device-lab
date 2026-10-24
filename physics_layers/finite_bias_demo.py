"""Bounded graphene finite-bias feedback and bound-occupation sensitivity pilot."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .bias_charge import BiasChargeDevice
from .graphene_feedback_demo import fixture
from .site_acceleration import solve_accelerated


def main():
    mesh, mapping, eq = fixture(0.03)
    # The same tiny graphene system as the equilibrium verification fixture.
    from ballistic_lab.pipeline.contracts import SquareDevice
    from ballistic_lab.transport.quantum import LatticeRequest, build_system

    system = build_system(SquareDevice((), 2 * 0.246e-9), LatticeRequest((0.7,)), ribbon=True)
    neutral = eq.solve(
        np.zeros(len(system.sites)), [2.5, 2.5], 300, tolerance=1e-7
    ).electrons_per_site
    rows = []
    for bias, reference in [(0.0, 0.0), (0.01, 0.0), (-0.01, 0.0), (0.01, -0.005), (0.01, 0.005)]:
        provider = BiasChargeDevice(system, reference_mu_ev=2.5 + reference)
        mus = [2.5 + bias / 2, 2.5 - bias / 2]
        frozen = provider.solve(np.full(len(system.sites), -0.03), mus, 300, tolerance=1e-7)
        result = solve_accelerated(
            mesh, mapping, provider, np.array(neutral), mus, 300, tolerance=1e-5
        )
        row = dict(
            bias_v=bias,
            bound_reference_ev=reference,
            frozen=asdict(frozen),
            screened=asdict(result.transport),
            potential_v=result.site_potential_v,
            residual=asdict(result.history[-1]),
            evaluations=len(result.history),
        )
        rows.append(row)
        print(json.dumps(row), flush=True)
    out = Path("results/physics-reference/finite-bias-feedback")
    out.mkdir(parents=True, exist_ok=True)
    sources = [
        "bias_charge",
        "finite_bias_demo",
        "equilibrium_charge",
        "lead_charge",
        "site_acceleration",
        "graphene_feedback_demo",
        "site_mesh",
        "poisson3d",
    ]
    record = dict(
        model="15-site graphene, 300 K, 30 mV dielectric gate box; EF 2.5 eV; fixed ideal lead Hamiltonians",
        limitations="Verification fixture, not winning rectifier. Bound-state occupations pinned to explicit reference. No calibrated contacts, phonons, mesh convergence or finite-frequency response.",
        source_sha256={
            s: hashlib.sha256(Path("physics_layers", s + ".py").read_bytes()).hexdigest()
            for s in sources
        },
        rows=rows,
    )
    (out / "result.json").write_text(json.dumps(record, indent=2))
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    base = sorted(rows[:3], key=lambda r: r["bias_v"])
    for key, label in [("frozen", "Unscreened 30 mV gate"), ("screened", "Charge + Poisson")]:
        axes[0].plot(
            [r["bias_v"] * 1000 for r in base],
            [r[key]["currents_a"][0] * 1e6 for r in base],
            "o-",
            label=label,
        )
    axes[0].set(xlabel="Reservoir bias (mV)", ylabel="Terminal current (µA)")
    axes[0].legend()
    for r in [rows[3], rows[1], rows[4]]:
        axes[1].plot(
            np.array(r["potential_v"]) * 1000,
            "o-",
            label=f"Reference {r['bound_reference_ev'] * 1000:g} meV",
        )
    axes[1].set(
        xlabel="Carbon site index",
        ylabel="Self-consistent potential (mV)",
        title="+10 mV: bound-occupation assumption",
    )
    axes[1].legend()
    fig.suptitle("Finite-bias graphene verification fixture | not a device-performance claim")
    fig.savefig(out / "comparison.png", dpi=160)


if __name__ == "__main__":
    main()
