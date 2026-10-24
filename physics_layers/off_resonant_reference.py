"""Independent finite-bias charge comparison away from the symmetric chain point."""
import hashlib
import json
from pathlib import Path
import numpy as np
from physics_layers.bias_charge import BiasChargeDevice
from physics_layers.lead_charge import LeadChargeDevice
from tests.test_lead_charge import chain


def main():
    system = chain()
    rows = []
    for temperature in (150, 600):
        try:
            expected = LeadChargeDevice(system, (-2, 2)).solve([0.7], [0.2, -0.1], temperature, tolerance=1e-7)
        except ArithmeticError as error:
            rows.append(dict(temperature_k=temperature, status='reference_rejected', reason=str(error)))
            continue
        for reference in (-0.1, 0.2):
            actual = BiasChargeDevice(system, reference_mu_ev=reference).solve([0.7], [0.2, -0.1], temperature, tolerance=1e-7)
            charge_error = float(np.max(np.abs(np.array(actual.electrons_per_site) - expected.electrons_per_site)))
            current_error = float(np.max(np.abs(np.array(actual.currents_a) - expected.currents_a)))
            rows.append(dict(temperature_k=temperature, reference_ev=reference, charge_error=charge_error, current_error_a=current_error))
            assert charge_error < 2e-6, rows[-1]
            assert current_error < 1e-11, rows[-1]
    sources = ['physics_layers/bias_charge.py', 'physics_layers/lead_charge.py', 'physics_layers/equilibrium_charge.py', 'physics_layers/off_resonant_reference.py', 'tests/test_lead_charge.py']
    record = dict(scope='Synthetic single-site chain verification; finite-band full integration versus equilibrium plus bias correction. No Poisson feedback or physical validation.', onsite_shift_ev=0.7, chemical_potentials_ev=[0.2, -0.1], rows=rows, sources={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources})
    output = Path('results/physics-reference/off-resonant-reference/result.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps(rows, indent=2))

if __name__ == '__main__':
    main()

