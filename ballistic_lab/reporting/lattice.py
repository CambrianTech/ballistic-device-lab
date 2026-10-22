"""Render static lattice transmission, never a rectification efficiency."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    output = Path("results/2026-10-22-lattice")
    data = json.loads((output / "lattice.json").read_text())
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    widths = sorted({d["width_m"] for d in data["devices"]})
    for col, width in enumerate(widths):
        for device in (d for d in data["devices"] if d["width_m"] == width):
            rows = device["spectrum"]
            energy = [r["energy_ev"] for r in rows]
            left_modes = np.array([r["modes"][0] for r in rows], dtype=float)
            matrix = np.array([r["transmission"] for r in rows])
            imbalance = np.divide(
                matrix[:, 3, 0] - matrix[:, 2, 0],
                left_modes,
                out=np.full_like(left_modes, np.nan),
                where=left_modes > 0,
            )
            axes[0, col].plot(energy, imbalance, "o-", label=device["id"])
            if device["id"] == "empty":
                axes[1, col].step(energy, left_modes, where="mid", label="Left/right")
                axes[1, col].step(
                    energy, [r["modes"][2] for r in rows], where="mid", label="Top/bottom"
                )
        axes[0, col].set_title(f"Nominal width {width * 1e9:.2f} nm")
        axes[0, col].axhline(0, color="gray", lw=0.7)
        axes[0, col].legend(ncol=2)
        axes[1, col].legend()
        axes[1, col].set_xlabel("Electron energy relative to onsite energy (eV)")
    axes[0, 0].set_ylabel("(Bottom − top transmission) / incoming left modes")
    axes[1, 0].set_ylabel("Propagating lead modes per spin")
    for axis in axes.flat:
        axis.grid(alpha=0.2)
    fig.suptitle("Graphene lattice check: contacts and energy change the transport")
    fig.text(
        0.5,
        0.015,
        "Static coherent transport • gaps: no incoming left mode • not DC output or efficiency",
        ha="center",
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    fig.savefig(output / "lattice-transmission.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    main()
