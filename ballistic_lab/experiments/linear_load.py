"""Finite-temperature linear terminal/load checkpoint with grid refinement."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system, solve_spectrum
from ballistic_lab.transport.reservoirs import ThermalRequest, solve_load, thermal_conductance
from ballistic_lab.validation.receipts import model_fingerprint


def main():
    output = Path("runs/linear-load")
    output.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(Path("results/2026-10-22-discovery/designs.json").read_text())
    selected = [dict(id="empty", excluded_polygons=[])] + [
        row for row in catalog if row["id"] in ("D00", "D12")
    ]
    thermal = ThermalRequest(fermi_ev=0.9, temperature_k=300)
    for row in selected:
        target = output / f"{row['id']}.json"
        if target.exists():
            raise FileExistsError(target)
        energies = tuple(np.linspace(0.57, 1.23, 257))
        request = LatticeRequest(energies)
        device = SquareDevice.from_geometry(row["excluded_polygons"], 60 * 0.246e-9)
        system = build_system(device, request)
        spectrum = solve_spectrum(system, request)
        fine, mass = thermal_conductance(spectrum, thermal)
        coarse, _ = thermal_conductance(spectrum[::2], thermal)
        error = float(np.max(abs(fine - coarse)) / np.max(abs(fine)))
        loads = []
        for resistance in (1e3, 1e4, 1e5, 1e6):
            positive = solve_load(fine, 0.001, resistance)
            negative = solve_load(fine, -0.001, resistance)
            coarse_output = solve_load(coarse, 0.001, resistance).output_voltage_v
            voltage_change = abs(positive.output_voltage_v - coarse_output)
            dc = (positive.output_voltage_v + negative.output_voltage_v) / 2
            if abs(dc) > 1e-15:
                raise RuntimeError("Linear model spuriously rectifies symmetric drive")
            loads.append(
                dict(
                    load_ohm=resistance,
                    positive=asdict(positive),
                    negative=asdict(negative),
                    symmetric_drive_dc_v=dc,
                    coarse_output_voltage_v=coarse_output,
                    output_grid_change_v=voltage_change,
                    output_converged=voltage_change <= 1e-9 + 0.01 * abs(positive.output_voltage_v),
                )
            )
        target.write_text(
            json.dumps(
                dict(
                    id=row["id"],
                    device_fingerprint=device.fingerprint,
                    width_m=device.width_m,
                    lattice_request=asdict(request),
                    thermal_request=asdict(thermal),
                    spectrum=spectrum,
                    conductance_s=fine.tolist(),
                    thermal_weight_mass=mass,
                    refinement_relative_max_error=error,
                    refinement_passed=error < 0.01,
                    loads=loads,
                    promotion_eligible=all(load["output_converged"] for load in loads),
                    model_fingerprint=model_fingerprint(),
                ),
                indent=2,
                allow_nan=False,
            )
        )
        print(f"{row['id']}: integration change {error:.3%}; DC={dc:.1e} V", flush=True)


if __name__ == "__main__":
    main()
