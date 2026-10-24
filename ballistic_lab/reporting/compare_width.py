"""Compare the completed 0.11 nm fixture with its saved same-grid baseline."""
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    paths = [Path('results/physics-reference') / folder / 'result.json' for folder in ('width-sensitivity-010-replay', 'width-sensitivity-011')]
    a, b = [json.loads(p.read_text()) for p in paths]
    if a['positions_m'] != b['positions_m'] or a['cutoff_sigma'] != b['cutoff_sigma']:
        raise ValueError('Coordinates or cutoff differ')
    changed = [k for k,v in a['source_sha256'].items() if b['source_sha256'].get(k) != v]
    if any(Path(k.replace('\\','/')).name != 'finite_width_feedback.py' for k in changed):
        raise ValueError('Baseline physics sources changed: ' + str(changed))
    current = b['rows'][0]
    matches = [r for r in a['rows'] if r['shape'] == current['shape'] and r['spacing_m'] == current['spacing_m']]
    if len(matches) != 1:
        raise ValueError('Unique matching grid required')
    previous = matches[0]
    result = dict(baseline_sigma_m=a['sigma_m'], candidate_sigma_m=b['sigma_m'],
        baseline_current_a=previous['transport']['currents_a'][0],
        candidate_current_a=current['transport']['currents_a'][0],
        relative_current_change=current['transport']['currents_a'][0]/previous['transport']['currents_a'][0]-1,
        max_site_potential_change_v=float(np.max(np.abs(np.array(current['potential_v'])-previous['potential_v']))),
        baseline_residual=previous['residual'], candidate_residual=current['residual'],
        input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        changed_baseline_sources=changed,
        limitation='Runner parameterization reviewed separately. Manifests cover physics_layers only. Not physical calibration.')
    with (paths[1].parent/'comparison.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

