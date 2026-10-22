"""Separate terminal voltage detection from useful DC power conversion."""

import json
import math


def metrics(result):
    voltage, power, supplied = (result[k] for k in ("dc_v", "dc_power_w", "input_power_w"))
    if not all(math.isfinite(v) for v in (voltage, power, supplied)) or supplied <= 0 or power < 0:
        raise ValueError("Finite positive input power and nonnegative DC load power required")
    return dict(
        loaded_responsivity_v_per_w=abs(voltage) / supplied,
        dc_efficiency=power / supplied,
        input_power_w=supplied,
        dc_power_w=power,
        dc_v=voltage,
    )


def render(rows, destination):
    records = [dict(candidate=r["candidate"], **metrics(r["phase64"])) for r in rows]
    (destination / "device-role.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    lines = [
        "### What useful function are we testing?\n",
        "**First target: a zero-DC-bias electrical signal detector.** Rectification turns an alternating input into a measurable DC signal. Power recovery is tracked separately.\n",
        "| Design | Terminal input (nW) | Loaded voltage response (V/W) | Useful DC (pW) | DC efficiency (%) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for r in records:
        lines.append(
            f"| {r['candidate']['key']} | {r['input_power_w'] * 1e9:.3f} | {r['loaded_responsivity_v_per_w']:.0f} | {r['dc_power_w'] * 1e12:.5f} | {100 * r['dc_efficiency']:.6f} |"
        )
    lines.append(
        "\nThese are finite-amplitude, quasistatic electrical-terminal values at 10 mV peak, 10 kΩ, 300 K and 0.9 eV in the frozen-potential model. Responsivity is |mean output voltage| / mean terminal input power; efficiency is mean(output voltage)² / (load resistance × mean input power). They are not optical responsivities, small-signal derivatives or measured performance.\n"
    )
    lines.append(
        "**Decision gates:** detector usefulness requires output-noise density, noise-equivalent input power, usable dynamic range and frequency response. Power-converter usefulness requires efficiency and delivered power across excitation and load. Neither application is qualified yet. The present search still optimizes nominal DC load power; this report does not silently change its objective. [Application qualification plan](docs/DEVICE-ROLE.md).\n"
    )
    return "\n".join(lines)
