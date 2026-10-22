"""Frozen-potential rectification baseline using archived nominal spectra."""

import gzip
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from ballistic_lab.transport.circuit import sinusoidal_cycle
from ballistic_lab.transport.finite_bias import FrozenPotentialModel
from ballistic_lab.transport.reservoirs import ThermalRequest


def main():
    output = Path("runs/finite-bias")
    if output.exists():
        raise RuntimeError("Preserve earlier results; use a fresh output directory")
    sources = {
        "empty": Path("results/2026-10-22-coverage/empty-nominal.json.gz"),
        "D00": Path("results/2026-10-22-convergence/D00-nominal.json.gz"),
        "D14": Path("results/2026-10-22-coverage/D14-nominal.json.gz"),
    }
    output.mkdir(parents=True)
    manifest = dict(
        model="frozen-potential reservoir-bias baseline; not self-consistent",
        fermi_ev=0.9,
        temperature_k=300,
        load_ohm=1e4,
        amplitudes_v=[0.001, 0.01, 0.05],
        phase_counts=[32, 64],
        dc_atol_v=1e-9,
        dc_rtol=0.01,
        inputs={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources.values()},
        source={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                Path(__file__),
                Path("ballistic_lab/transport/finite_bias.py"),
                Path("ballistic_lab/transport/circuit.py"),
                Path("ballistic_lab/transport/reservoirs.py"),
            )
        },
    )
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    results = []
    for candidate, path in sources.items():
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            spectrum = json.load(stream)["spectrum"]
        for amplitude in manifest["amplitudes_v"]:
            levels = []
            for stride in (4, 2, 1):
                selected = spectrum[::stride]
                model = FrozenPotentialModel.from_spectrum(selected, ThermalRequest(0.9, 300))
                cycle = sinusoidal_cycle(model, amplitude, 1e4, 64)
                levels.append(dict(count=len(selected), cycle=asdict(cycle)))
            phase_coarse = sinusoidal_cycle(model, amplitude, 1e4, 32)
            dc = cycle.dc_output_v
            energy_changes = [
                abs(b["cycle"]["dc_output_v"] - a["cycle"]["dc_output_v"])
                for a, b in zip(levels, levels[1:])
            ]
            energy_passed = all(
                change <= 1e-9 + 0.01 * abs(level["cycle"]["dc_output_v"])
                for change, level in zip(energy_changes, levels[1:])
            )
            phase_change = abs(dc - phase_coarse.dc_output_v)
            row = dict(
                candidate=candidate,
                amplitude_v=amplitude,
                levels=levels,
                energy_changes_v=energy_changes,
                energy_converged=energy_passed,
                phase_change_v=phase_change,
                phase_converged=phase_change <= 1e-9 + 0.01 * abs(dc),
            )
            results.append(row)
            (output / "summary.json").write_text(
                json.dumps(results, indent=2, allow_nan=False), encoding="utf-8"
            )
            print(
                f"{candidate} {amplitude:g} V: DC {dc * 1e6:.6g} uV; energy={energy_passed}; phase={row['phase_converged']}",
                flush=True,
            )


if __name__ == "__main__":
    main()
