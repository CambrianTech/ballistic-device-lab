"""Dense sampled spectra and observable-level refinement, without smoothing."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ballistic_lab.transport.reservoirs import KB_EV

LABELS = {"empty": "Empty control", "D00": "D00 · beveled anchor", "D12": "D12 · free profile"}
COLORS = {"empty": "#65758b", "D00": "#d4771b", "D12": "#139477"}


def main():
    output = Path("results/2026-10-22-linear-load")
    datasets = [json.loads((output / f"{key}.json").read_text()) for key in LABELS]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.5))
    for data in datasets:
        key = data["id"]
        color, label = COLORS[key], LABELS[key]
        rows = data["spectrum"]
        energy = np.array([r["energy_ev"] for r in rows])
        t = np.array([r["transmission"] for r in rows])
        n = np.array([r["modes"][0] for r in rows], float)
        kwargs = dict(color=color, label=label, lw=1.2)
        axes[0, 0].plot(energy, t[:, 1, 0], **kwargs)
        axes[0, 1].plot(energy, n - t[:, 0, 0], **kwargs)
        imbalance = np.divide(t[:, 3, 0] - t[:, 2, 0], n, out=np.full_like(n, np.nan), where=n > 0)
        axes[1, 0].plot(energy, imbalance, **kwargs)
        load = next(r for r in data["loads"] if r["load_ohm"] == 1e4)
        coarse = load["coarse_output_voltage_v"] * 1e6
        fine = load["positive"]["output_voltage_v"] * 1e6
        axes[1, 1].plot([129, 257], [coarse, fine], "o-", **kwargs)
        axes[1, 1].annotate(
            f"{fine:.2f} µV",
            (257, fine),
            xytext=(7, 0),
            textcoords="offset points",
            va="center",
            color=color,
        )
    thermal = datasets[0]["thermal_request"]
    mu, kt = thermal["fermi_ev"], KB_EV * thermal["temperature_k"]
    for axis in (axes[0, 0], axes[0, 1], axes[1, 0]):
        axis.axvspan(mu - 2 * kt, mu + 2 * kt, color="#608fc9", alpha=0.12)
        axis.axvline(mu, color="#608fc9", lw=0.8, ls="--")
        axis.set_xlabel("Electron energy (eV)")
    axes[0, 0].set(
        title="A · Transmission to the opposite contact", ylabel="T(right ← left), per spin"
    )
    axes[0, 1].set(
        title="B · Total transmission out of the left lead", ylabel="N(left) − reflection, per spin"
    )
    axes[1, 0].set(
        title="C · Directional imbalance for left injection",
        ylabel="[T(bottom ← left) − T(top ← left)] / N(left)",
    )
    axes[1, 0].axhline(0, color="gray", lw=0.6)
    axes[1, 1].set(
        title="D · Loaded output needs tighter convergence",
        xlabel="Energy-grid points",
        ylabel="Output amplitude at 10 kΩ (µV)",
        xlim=(110, 320),
    )
    axes[1, 1].set_xticks([129, 257])
    axes[0, 0].legend(fontsize=9)
    for axis in axes.flat:
        axis.grid(alpha=0.2)
    fig.suptitle("Dense lattice spectra: 257 computed energies per geometry", fontsize=16)
    fig.text(
        0.5,
        0.025,
        "14.76 nm cavity · shaded: EF ± 2kBT at 300 K · straight segments join samples; no smoothing\nLinear response only; panel D uses balanced drive. These are not rectification-efficiency curves.",
        ha="center",
        fontsize=10,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(output / "dense-spectra.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
