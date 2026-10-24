"""Independent analytic impurity-chain reference including its discrete pole."""
import argparse
import json
import hashlib
import platform
from importlib.metadata import version
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.special import expit
from scipy.constants import Boltzmann, elementary_charge, h
from physics_layers.bias_charge import BiasChargeDevice
from tests.test_lead_charge import chain


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--near-bound', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('results/physics-reference/impurity-bound-reference'))
    args = parser.parse_args()
    if (args.output / 'result.json').exists():
        parser.error('Result already exists; choose a new output directory')
    root = Path(__file__).resolve().parents[1]
    source_paths = sorted((root / 'physics_layers').glob('*.py')) + [root / 'tests/test_lead_charge.py']
    provenance = dict(python=platform.python_version(), packages={name: version(name) for name in ('numpy', 'scipy', 'kwant')},
                      source_sha256={p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
                      near_bound=args.near_bound, solver_tolerance=1e-7, reference_epsabs=1e-10,
                      chemical_potentials_ev=[.2, -.1], spin=2)
    rows = []
    for u in (-0.7, 0.7):
        energy = np.sign(u) * np.sqrt(4 + u*u)
        weight = abs(u) / np.sqrt(4 + u*u)
        density = lambda e: np.sqrt(max(0, 4-e*e)) / (np.pi*(4-e*e+u*u))
        total = quad(density, -2, 2, epsabs=1e-11)[0] + weight
        assert abs(total-1) < 1e-9
        for temperature in (150, 600):
            kt = Boltzmann*temperature/elementary_charge
            f = lambda e, mu: expit((mu-e)/kt)
            for reference in ((energy-.02, energy+.02) if args.near_bound else (-0.1, 0.2)):
                charge = quad(lambda e: density(e)*(f(e,.2)+f(e,-.1)), -2, 2, epsabs=1e-10)[0] + 2*weight*f(energy, reference)
                current = 2*elementary_charge**2/h*quad(lambda e: (4-e*e)/(4-e*e+u*u)*(f(e,.2)-f(e,-.1)), -2, 2, epsabs=1e-10)[0]
                actual = BiasChargeDevice(chain(), reference_mu_ev=reference).solve([u], [.2,-.1], temperature, tolerance=1e-7)
                ce = abs(actual.electrons_per_site[0]-charge)
                ie = float(np.max(np.abs(np.array(actual.currents_a)-[current,-current])))
                assert ce < 2e-6 and ie < 1e-11, (ce, ie)
                rows.append(dict(onsite_ev=u, temperature_k=temperature, reference_ev=reference, bound_energy_ev=float(energy), bound_weight=float(weight), sum_rule=total, charge_electrons=float(actual.electrons_per_site[0]), current_a=float(actual.currents_a[0]), charge_error=float(ce), current_error_a=ie))
    out=args.output
    out.mkdir(parents=True, exist_ok=True)
    with (out/'result.json').open('x') as stream:
        json.dump(dict(scope='Analytic synthetic chain verification, no Poisson feedback or physical validation', rows=rows, provenance=provenance), stream, indent=2)
    print('cases',len(rows),'max charge error',max(r['charge_error'] for r in rows),'max current error',max(r['current_error_a'] for r in rows))

if __name__ == '__main__':
    main()
