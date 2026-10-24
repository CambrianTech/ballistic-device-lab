"""Independent analytic impurity-chain reference including its discrete pole."""
import json
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.special import expit
from scipy.constants import Boltzmann, elementary_charge, h
from physics_layers.bias_charge import BiasChargeDevice
from tests.test_lead_charge import chain


def main():
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
            for reference in (-0.1, 0.2):
                charge = quad(lambda e: density(e)*(f(e,.2)+f(e,-.1)), -2, 2, epsabs=1e-10)[0] + 2*weight*f(energy, reference)
                current = 2*elementary_charge**2/h*quad(lambda e: (4-e*e)/(4-e*e+u*u)*(f(e,.2)-f(e,-.1)), -2, 2, epsabs=1e-10)[0]
                actual = BiasChargeDevice(chain(), reference_mu_ev=reference).solve([u], [.2,-.1], temperature, tolerance=1e-7)
                ce = abs(actual.electrons_per_site[0]-charge)
                ie = float(np.max(np.abs(np.array(actual.currents_a)-[current,-current])))
                assert ce < 2e-6 and ie < 1e-11, (ce, ie)
                rows.append(dict(onsite_ev=u, temperature_k=temperature, reference_ev=reference, bound_energy_ev=float(energy), bound_weight=float(weight), sum_rule=total, charge_error=float(ce), current_error_a=ie))
    out=Path('results/physics-reference/impurity-bound-reference')
    out.mkdir(parents=True, exist_ok=True)
    with (out/'result.json').open('x') as stream:
        json.dump(dict(scope='Analytic synthetic chain verification, no Poisson feedback or physical validation', rows=rows), stream, indent=2)
    print('cases',len(rows),'max charge error',max(r['charge_error'] for r in rows),'max current error',max(r['current_error_a'] for r in rows))

if __name__ == '__main__':
    main()
