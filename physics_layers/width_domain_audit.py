"""Audit Gaussian support using saved fixture coordinates; no transport solves."""
import hashlib
import json
from pathlib import Path
import numpy as np
from physics_layers.gaussian_site_mesh import GaussianSiteMeshMap


def main():
    source = Path('results/physics-reference/finite-width-feedback/result.json')
    out = Path('results/physics-reference/width-domain-audit')
    if (out / 'result.json').exists():
        raise FileExistsError(out / 'result.json')
    data = json.loads(source.read_text())
    positions = np.array(data['positions_m'])
    rows = []
    for grid in data['rows']:
        shape, spacing = tuple(grid['shape']), tuple(grid['spacing_m'])
        fixed = np.full(shape, 0.03)
        fixed[1:-1, 1:-1, 1:-1] = np.nan
        for width in (0.05, 0.08, 0.10, 0.11, 0.119, 0.12, 0.13):
            row = dict(spacing_nm=spacing[0]*1e9, sigma_nm=width)
            try:
                mapping = GaussianSiteMeshMap(shape, spacing, (0,0,0), positions, width*1e-9)
                rho = mapping.deposit_charge(np.ones(len(positions)), fixed)
                recovered = float(rho.sum()*np.prod(spacing))
                if not np.isclose(recovered, len(positions), rtol=1e-12):
                    raise AssertionError('Charge conservation failed')
                row.update(status='admissible', normalized_charge_sum=recovered)
            except ValueError as error:
                row.update(status='rejected', reason=str(error))
            rows.append(row)
    record = dict(input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), Path('physics_layers/gaussian_site_mesh.py'), Path('physics_layers/site_mesh.py')]},
                  cutoff_sigma=5, rows=rows, scope='Numerical domain audit, not physical calibration or transport evidence')
    out.mkdir(parents=True, exist_ok=True)
    with (out/'result.json').open('x') as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
