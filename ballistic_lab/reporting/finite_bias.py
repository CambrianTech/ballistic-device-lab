"""Plot the archived fixed-potential DC test without conflating AC and DC."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    folder = Path("results/2026-10-22-finite-bias")
    rows = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for candidate, color in (("D00", "#516580"), ("D14", "#087f8c"), ("empty", "#b57928")):
        selected = [r for r in rows if r["candidate"] == candidate]
        amplitudes = [r["amplitude_v"] * 1e3 for r in selected]
        dc = [abs(r["levels"][-1]["cycle"]["dc_output_v"]) * 1e6 for r in selected]
        axes[0].loglog(amplitudes, dc, "-", color=color, label=candidate)
        for x, y, r in zip(amplitudes, dc, selected, strict=True):
            axes[0].plot(x, y, "o" if r["energy_converged"] else "x", color=color)
        if candidate != "empty":
            cycle = selected[1]["levels"][-1]["cycle"]
            samples = cycle["samples"]
            phase = np.arange(len(samples)) * 360 / len(samples)
            axes[1].plot(
                phase, [s["output_v"] * 1e6 for s in samples], color=color, label=candidate
            )
            axes[1].axhline(cycle["dc_output_v"] * 1e6, color=color, linestyle=":")
    axes[0].set(
        xlabel="Sinusoidal drive amplitude (mV)",
        ylabel="DC output magnitude (µV)",
        title="Bevel leads the DC baseline",
    )
    axes[1].set(
        xlabel="Drive phase (degrees)",
        ylabel="Instantaneous output (µV)",
        title="10 mV drive: large AC is not large DC",
    )
    for ax in axes:
        ax.grid(alpha=0.2)
        ax.legend()
    fig.suptitle("Fixed-potential test · reservoir nonlinearity only", fontweight="bold")
    fig.text(
        0.5,
        0.015,
        "300 K occupations · 0.9 eV · 10 kΩ · × = unresolved energy integration; dotted = cycle mean",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(folder / "finite-bias.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
