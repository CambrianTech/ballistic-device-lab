"""Compare immutable coarse/fine feedback records at the same cloud width."""
import argparse
import hashlib
import json
from pathlib import Path


def validate_dimensions(record):
    sites = len(record['positions_m'])
    if not sites or any(len(p) != 3 for p in record['positions_m']):
        raise ValueError('Nonempty three-dimensional site positions required')
    for row in record['rows']:
        if len(row['shape']) != 3 or len(row['spacing_m']) != 3:
            raise ValueError('Three mesh dimensions required')
        if len(row['potential_v']) != sites:
            raise ValueError('Every site must have a potential')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('coarse', type=Path)
    parser.add_argument('fine', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    records = [json.loads(p.read_text()) for p in (args.coarse, args.fine)]
    for record in records:
        validate_dimensions(record)
    a, b = records
    for key in ('sigma_m', 'cutoff_sigma', 'positions_m', 'source_sha256'):
        if a[key] != b[key]:
            raise ValueError(f'Mismatched {key}')
    if any(len(r['rows']) != 1 for r in records):
        raise ValueError('One grid per input required')
    x, y = (r['rows'][0] for r in records)
    for n, m, h, k in zip(x['shape'], y['shape'], x['spacing_m'], y['spacing_m']):
        if not k < h or abs((n - 1) * h - (m - 1) * k) > 1e-20:
            raise ValueError('Require finer spacing and identical domain')
    result = dict(
        sigma_m=a['sigma_m'],
        coarse_spacing_m=x['spacing_m'], fine_spacing_m=y['spacing_m'],
        coarse_current_a=x['transport']['currents_a'][0],
        fine_current_a=y['transport']['currents_a'][0],
        relative_current_change=y['transport']['currents_a'][0] / x['transport']['currents_a'][0] - 1,
        max_site_potential_change_v=max(abs(u-v) for u,v in zip(x['potential_v'], y['potential_v'])),
        coarse_residual=x['residual'], fine_residual=y['residual'],
        input_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.coarse, args.fine)},
        limitation='Two-grid sensitivity, not asymptotic convergence or physical calibration. Source manifest covers physics_layers only.')
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
