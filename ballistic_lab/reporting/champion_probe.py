"""Bounded, reproducible champion mutations outside live campaign scoring."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from ballistic_lab.geometry.families import FAMILIES, geometry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=261026)
    args = parser.parse_args()
    data = args.snapshot.read_bytes()
    state = json.loads(data)
    parent = state['retained_champion']
    if not (parent.get('energy_converged') and parent.get('phase_converged')):
        raise ValueError('Qualified retained champion required')
    candidate = parent['candidate']
    bounds = np.array(FAMILIES[candidate['family']].bounds)
    low, width = bounds[:, 0], bounds[:, 1]-bounds[:, 0]
    unit = (np.array(candidate['parameters'])-low)/width
    rng = np.random.default_rng(args.seed)
    children = []
    for index, scale in enumerate((.02, .02, .08, .08)):
        child = 1-abs(np.mod(unit+rng.normal(0, scale, len(unit)), 2)-1)
        parameters = low+child*width
        children.append(dict(key=f'champion-probe-{args.seed}-{index}',
            family=candidate['family'], parameters=parameters.tolist(),
            origin=f"mutation of {candidate['key']}", mutation_sigma=scale,
            obstacles=[p.tolist() for p in geometry(candidate['family'], parameters)]))
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = dict(snapshot=str(args.snapshot), snapshot_sha256=hashlib.sha256(data).hexdigest(),
        seed=args.seed, parent=parent, children=children,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path('ballistic_lab').rglob('*.py')},
        limitation='Four fixed-potential mutations; no evidence yet for optimal spawn allocation or physical novelty.')
    (args.output/'selection.json').write_text(json.dumps(receipt, indent=2))
    spectra = args.output/'spectra'
    spectra.mkdir()
    from ballistic_lab.pipeline.dc_continuous import task
    results = []
    for child in children:
        print('Evaluating', child['key'], flush=True)
        result = task(child, spectra, True)
        (args.output/(child['key']+'.json')).write_text(json.dumps(result, indent=2))
        results.append(result)
        print('Completed', child['key'], result.get('phase64'), flush=True)
    (args.output/'result.json').write_text(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
