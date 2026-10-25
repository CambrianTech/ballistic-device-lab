"""One deterministic lower-half holdout; independent of live search selection."""
import argparse
import hashlib
import json
from pathlib import Path

def select_holdout(rows, family=None, excluded_keys=()):
    ranked=sorted((r for r in rows if family is None or r['candidate']['family']==family),
                  key=lambda r:(r['levels'][0]['dc_power_w'],r['candidate']['key']))
    pool=[r for r in ranked[:len(ranked)//2] if not r.get('phase64') and r['candidate']['key'] not in excluded_keys]
    if not pool:
        raise ValueError('No unrefined lower-half candidates in the requested population')
    chosen=min(pool,key=lambda r:hashlib.sha256(r['candidate']['key'].encode()).hexdigest())
    return chosen, len(pool), len(ranked)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,default=Path('runs/fresh-discovery-continuous-v1/round-000021.json'))
    parser.add_argument('--output',type=Path,default=Path('results/fresh-discovery/continuous-v1-low-score-holdout'))
    parser.add_argument('--family',help='Restrict population before taking its lower half')
    parser.add_argument('--exclude-key',action='append',default=[],help='Previously checked candidate; repeat for multiple keys')
    args=parser.parse_args()
    source=args.snapshot
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    if (out/'selection.json').exists():
        raise FileExistsError(out/'selection.json')
    state=json.loads(source.read_text())
    chosen,pool_size,population=select_holdout(state['rows'],args.family,args.exclude_key)
    selection=dict(snapshot=str(source),snapshot_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        rule='Lowest SHA256(candidate key) among lower-half coarse-power rows without phase64',
        family_filter=args.family,excluded_keys=args.exclude_key,pool_size=pool_size,population=population,candidate=chosen,
        limitation='One deterministic diagnostic, not an unbiased population estimate')
    (out/'selection.json').write_text(json.dumps(selection,indent=2))
    print(chosen['candidate']['key'],flush=True)
    spectra=out/'spectra';spectra.mkdir()
    from ballistic_lab.pipeline.dc_continuous import task
    result=task(chosen['candidate'],spectra,True)
    (out/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(energy_converged=result.get('energy_converged'),phase_converged=result.get('phase_converged'),phase64=result.get('phase64'))),flush=True)


if __name__=='__main__': main()
