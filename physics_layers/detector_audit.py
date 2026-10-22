"""Reproducible equilibrium electrical detector audit of frozen selected spectra."""

import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from ballistic_lab.transport.circuit import sinusoidal_cycle
from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.reservoirs import ThermalRequest, thermal_conductance
from physics_layers.noise import equilibrium_output_noise
from verification_lab.worker import selected


def evaluate(spectrum):
    thermal = ThermalRequest(0.9, 300)
    g, mass = thermal_conductance(spectrum, thermal)
    noise = equilibrium_output_noise(g, 300, 1e4)
    model = FrozenPotentialModel.from_spectrum(spectrum, thermal)
    points = []
    for amplitude in (0.001, 0.002, 0.005, 0.01):
        result = sinusoidal_cycle(model, amplitude, 1e4, 64)
        points.append(
            dict(
                amplitude_v=amplitude,
                dc_v=result.dc_output_v,
                input_w=result.mean_input_power_w,
                dc_power_w=result.dc_load_power_w,
            )
        )
    slope = (points[1]["dc_v"] - points[0]["dc_v"]) / (points[1]["input_w"] - points[0]["input_w"])
    return dict(
        noise=asdict(noise),
        thermal_mass=mass,
        points=points,
        weak_interval_responsivity_v_per_w=abs(slope),
        equilibrium_nep_estimate_w_per_root_hz=noise.voltage_v_per_root_hz / abs(slope)
        if slope
        else None,
    )


def main():
    output = Path("results/physics-reference/detector-audit")
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for row in selected():
        candidate = row["candidate"]
        path = Path("runs/dc-continuous/spectra") / f"{candidate['key']}.json.gz"
        if not path.exists():
            path = Path("results/2026-10-22-dc-wide") / path.name
        raw = path.read_bytes()
        record = json.loads(gzip.decompress(raw))
        if record["candidate"]["obstacles"] != candidate["obstacles"]:
            raise ValueError("Spectrum geometry mismatch")
        fine = evaluate(record["spectrum"])
        coarse = evaluate(record["spectrum"][::2])
        a = fine["equilibrium_nep_estimate_w_per_root_hz"]
        b = coarse["equilibrium_nep_estimate_w_per_root_hz"]
        converged = a is not None and b is not None and abs(a - b) <= 0.01 * abs(a)
        records.append(
            dict(
                candidate=candidate,
                source_path=str(path),
                source_sha256=hashlib.sha256(raw).hexdigest(),
                fine=fine,
                coarse=coarse,
                nep_grid_converged=converged,
                qualification="incomplete: equilibrium noise only; frequency response and self-consistent electrostatics absent",
            )
        )
    sources = list(Path("physics_layers").glob("*.py")) + list(
        Path("ballistic_lab/transport").glob("*.py")
    )
    (output / "source.json").write_text(
        json.dumps({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, indent=2),
        encoding="utf-8",
    )
    (output / "results.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    lines = [
        "# Equilibrium electrical detector audit\n",
        "| Design | Noise (nV/√Hz) | Weak-interval response (V/W) | Equilibrium NEP estimate (pW/√Hz) | Grid check |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for record in records:
        r = record["fine"]
        lines.append(
            f"| {record['candidate']['key']} | {r['noise']['total_v2_per_hz'] ** 0.5 * 1e9:.3f} | {r['weak_interval_responsivity_v_per_w']:.1f} | {r['equilibrium_nep_estimate_w_per_root_hz'] * 1e12:.3f} | {'pass' if record['nep_grid_converged'] else 'unresolved'} |"
        )
    lines.append(
        "\nFixed-potential 300 K electrical terminal model, 10 kΩ load, ideal voltage-clamped inputs. Response is the secant between 1 and 2 mV peak; 5 and 10 mV points are retained in JSON. Noise includes correlated device and load thermal noise. Grid check compares the saved full grid with every second energy point. This is not optical NEP or a validated finite-drive detector: excess/1/f/readout noise, bandwidth, electrostatic feedback and experimental reproduction remain absent. No search score is changed.\n"
    )
    (output / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(records)} detector audits to {output}")


if __name__ == "__main__":
    main()
