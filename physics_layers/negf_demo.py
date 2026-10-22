"""Reproducible two-site charge-feedback benchmark, not a graphene device."""

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .negf_reference import WideBandDevice, solve_hartree


def main():
    root = Path("results/physics-reference/negf-two-site")
    root.mkdir(parents=True, exist_ok=True)
    ham = [[0.08, -0.12], [-0.12, -0.04]]
    gammas = [np.diag([0.08, 0]), np.diag([0, 0.12])]
    kernel = [[0.3, 0.08], [0.08, 0.3]]
    device = WideBandDevice(ham, gammas)
    reference = device.solve([0, 0], [0, 0], 300, tolerance=1e-11).electrons_per_site
    rows = []
    for bias in np.linspace(-0.1, 0.1, 9):
        mus = [bias / 2, -bias / 2]
        frozen = device.solve([0, 0], mus, 300)
        coupled = solve_hartree(device, mus, 300, reference, kernel, [0, 0])
        refined = solve_hartree(
            device,
            mus,
            300,
            reference,
            kernel,
            [0, 0],
            tolerance_ev=1e-9,
            quadrature_tolerance=1e-11,
        )
        current_change = abs(coupled.transport.currents_a[0] - refined.transport.currents_a[0])
        charge_change = float(
            np.max(
                abs(
                    np.array(coupled.transport.electrons_per_site)
                    - refined.transport.electrons_per_site
                )
            )
        )
        if current_change > 1e-11 or charge_change > 1e-6:
            raise ArithmeticError("Demo refinement failed")
        rows.append(
            dict(
                bias_v=float(bias),
                frozen=asdict(frozen),
                coupled=asdict(refined),
                refinement_current_a=current_change,
                refinement_electrons=charge_change,
            )
        )
    metadata = dict(
        model="two-site wide-band Hartree verification fixture",
        temperature_k=300,
        hamiltonian_ev=ham,
        broadenings_ev=[g.tolist() for g in gammas],
        interaction_ev=kernel,
        reference_electrons=reference,
        source_sha256={
            str(p): sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__), Path(__file__).with_name("negf_reference.py")]
        },
        rows=rows,
    )
    (root / "results.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    biases = np.array([r["bias_v"] for r in rows]) * 1000
    axes[0].plot(
        biases,
        [r["frozen"]["currents_a"][0] * 1e6 for r in rows],
        "o--",
        label="Fixed onsite energies",
    )
    axes[0].plot(
        biases,
        [r["coupled"]["transport"]["currents_a"][0] * 1e6 for r in rows],
        "s-",
        label="Charge feedback",
    )
    axes[0].set(xlabel="Reservoir energy separation / e (mV)", ylabel="Terminal current (µA)")
    axes[0].legend()
    for site in range(2):
        axes[1].plot(
            biases,
            [r["coupled"]["onsite_shift_ev"][site] * 1000 for r in rows],
            "o-",
            label=f"Site {site}",
        )
    axes[1].set(
        xlabel="Reservoir energy separation / e (mV)", ylabel="Self-consistent onsite shift (meV)"
    )
    axes[1].legend()
    fig.suptitle("Nonequilibrium charge feedback · two-site reference, 300 K")
    fig.savefig(root / "comparison.png", dpi=160)
    plt.close(fig)
    print("9 bias points passed current/charge refinement; results:", root)


if __name__ == "__main__":
    main()
