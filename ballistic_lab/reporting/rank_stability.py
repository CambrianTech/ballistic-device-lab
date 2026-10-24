"""Audit screening/refinement rank reversals within the qualified subset."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = json.loads(args.snapshot.read_text())
    rows = []
    for r in data['rows']:
        if not (r.get('energy_converged') and r.get('phase_converged') and r.get('phase64')):
            continue
        coarse = next(v for v in r['levels'] if v['count'] == 257)
        rows.append(dict(key=r['candidate']['key'], family=r['candidate']['family'],
                         coarse_power_w=coarse['dc_power_w'], refined_power_w=r['phase64']['dc_power_w']))
    if len(rows) < 2 or len({r['key'] for r in rows}) != len(rows):
        raise ValueError('Need at least two uniquely identified qualified candidates')
    pairs = list(itertools.combinations(rows, 2))
    reversals = [dict(a=a['key'], b=b['key']) for a,b in pairs
                 if (a['coarse_power_w']-b['coarse_power_w'])*(a['refined_power_w']-b['refined_power_w']) < 0]
    ties = sum(a['coarse_power_w'] == b['coarse_power_w'] or a['refined_power_w'] == b['refined_power_w'] for a,b in pairs)
    for field in ('coarse', 'refined'):
        for rank, row in enumerate(sorted(rows, key=lambda r: (-r[field+'_power_w'], r['key'])), 1):
            row[field+'_rank'] = rank
    coarse_best = min(rows, key=lambda r:r['coarse_rank'])['key']
    refined_best = min(rows, key=lambda r:r['refined_rank'])['key']
    result = dict(generation=data['round'], population=len(data['rows']), qualified=len(rows),
                  pair_count=len(pairs), tied_pairs=ties, reversed_pairs=len(reversals),
                  coarse_best=coarse_best, refined_best=refined_best,
                  max_rank_shift=max(abs(r['coarse_rank']-r['refined_rank']) for r in rows),
                  snapshot_sha256=hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
                  rows=rows, reversals=reversals,
                  limitation='Selected qualified subset only; cannot estimate missed winners among unrefined candidates. Fixed-potential simulation, not physical validation.')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'result.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    (args.output/'README.md').write_text(
        f"# Does refinement reorder screened candidates?\n\n"
        f"At generation {data['round']}, **{len(rows)} of {len(data['rows'])} candidates** have passed energy and phase convergence checks. "
        f"Within that selected subset, **{len(reversals)} of {len(pairs)} pairs reverse order** between the shared 257-point screening power and refined 64-phase power ({ties} tied pairs). "
        f"The largest ordinal rank shift is **{result['max_rank_shift']} places**. Ties use candidate keys for deterministic ordering.\n\n"
        f"Screening leader: `{coarse_best}`. Refined leader: `{refined_best}`.\n\n"
        "This diagnoses numerical rank stability among candidates already selected for refinement. It does not measure the false-negative rate of early screening: unrefined candidates remain unresolved. "
        "It therefore cannot justify tightening screening or establish that the search is finding all promising designs. No live scoring or selection was changed.\n\n"
        f"Reproduce: `python -m ballistic_lab.reporting.rank_stability {args.snapshot.as_posix()} <new-output-directory>`. "
        "The JSON includes every paired score, reversed pair, and the immutable input SHA-256. These are fixed-potential simulation results, not physical validation or novelty evidence.\n",
        encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','reversals')}, indent=2))


if __name__ == '__main__':
    main()
