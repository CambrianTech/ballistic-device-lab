"""Show linear loaded transfer and explicitly distinguish AC heat from DC."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    output = Path("results/2026-10-22-linear-load")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for path in sorted(output.glob("*.json")):
        data = json.loads(path.read_text())
        loads = data["loads"]
        resistance = [row["load_ohm"] for row in loads]
        voltage = [row["positive"]["output_voltage_v"] * 1e6 for row in loads]
        # Linear response to 1 mV PEAK sinusoid: mean resistor heat = peak/2.
        power = [row["positive"]["load_power_w"] * 0.5e15 for row in loads]
        axes[0].semilogx(resistance, voltage, "o-", label=data["id"])
        axes[1].semilogx(resistance, power, "o-", label=data["id"])
    axes[0].set_ylabel("Output amplitude (microvolts)")
    axes[1].set_ylabel("Mean AC resistor heating (fW)")
    for axis in axes:
        axis.set_xlabel("Load resistance (ohms)")
        axis.legend()
        axis.grid(alpha=0.2)
    fig.suptitle("Linear circuit checkpoint: 1 mV peak drive, 300 K occupations")
    fig.text(
        0.5,
        0.015,
        "All cases: mean output voltage = 0; delivered DC power = 0. No phonon scattering modeled.",
        ha="center",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(output / "linear-load.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    main()
