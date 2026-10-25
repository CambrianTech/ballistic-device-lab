"""Separate unrefined candidates from attempted, unresolved refinement."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('snapshot', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    data = json.loads(a.snapshot.read_text())
    groups = collections.defaultdict(list)
    for row in data['rows']:
        counts = [level['count'] for level in row['levels']]
        if row.get('energy_converged') and row.get('phase_converged') and row.get('phase64'):
            status = 'converged'
        elif max(counts) > 257:
            status = 'refined_unresolved'
        else:
            status = 'screened_only'
        groups[status].append(dict(key=row['candidate']['key'], max_energy_points=max(counts),
                                  energy_converged=bool(row.get('energy_converged')),
                                  phase_converged=bool(row.get('phase_converged'))))
    result = dict(generation=data['round'], snapshot_sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),
                  counts={k:len(groups[k]) for k in ('converged','refined_unresolved','screened_only')}, groups=dict(groups),
                  scope='Completed snapshot only. Screened-only means untested at refinement, not failed convergence; no physical validation.')
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output/'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
