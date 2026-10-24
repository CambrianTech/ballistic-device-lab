"""Compare proposal responses at the shared screening resolution."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text())
    rows = []
    for row in snapshot['rows']:
        level = next(x for x in row['levels'] if x['count'] == 257)
        rows.append(dict(key=row['candidate']['key'], family=row['candidate']['family'],
                         dc_uv=level['dc_v'] * 1e6,
                         qualified=bool(row.get('energy_converged') and row.get('phase_converged'))))
    families = {}
    for family in sorted({r['family'] for r in rows}):
        selected = [r for r in rows if r['family'] == family]
        values = [r['dc_uv'] for r in selected]
        families[family] = dict(count=len(values), minimum_uv=min(values), maximum_uv=max(values),
                                median_absolute_uv=statistics.median(map(abs, values)),
                                positive=sum(v > 0 for v in values), negative=sum(v < 0 for v in values),
                                qualified=sum(r['qualified'] for r in selected))
    result = dict(snapshot=args.snapshot.as_posix(),
                  snapshot_sha256=hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
                  generation=snapshot['round'], screening_energy_points=257,
                  scope='Common coarse fixed-potential screening observable, not converged rankings or physical novelty.',
                  families=families, rows=rows)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(families, indent=2))


if __name__ == '__main__':
    main()
