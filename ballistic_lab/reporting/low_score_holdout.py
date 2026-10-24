"""One deterministic lower-half holdout; independent of live search selection."""
import hashlib
import json
from pathlib import Path
from ballistic_lab.pipeline.dc_continuous import task


def main():
    source=Path('runs/fresh-discovery-continuous-v1/round-000021.json')
    out=Path('results/fresh-discovery/continuous-v1-low-score-holdout')
    out.mkdir(parents=True,exist_ok=True)
    if (out/'selection.json').exists():
        raise FileExistsError(out/'selection.json')
    state=json.loads(source.read_text())
    ranked=sorted(state['rows'],key=lambda r:(r['levels'][0]['dc_power_w'],r['candidate']['key']))
    pool=[r for r in ranked[:len(ranked)//2] if not r.get('phase64')]
    chosen=min(pool,key=lambda r:hashlib.sha256(r['candidate']['key'].encode()).hexdigest())
    selection=dict(snapshot=str(source),snapshot_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        rule='Lowest SHA256(candidate key) among lower-half coarse-power rows without phase64',
        pool_size=len(pool),population=len(ranked),candidate=chosen,
        limitation='One deterministic diagnostic, not an unbiased population estimate')
    (out/'selection.json').write_text(json.dumps(selection,indent=2))
    print(chosen['candidate']['key'],flush=True)
    spectra=out/'spectra';spectra.mkdir()
    result=task(chosen['candidate'],spectra,True)
    (out/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(energy_converged=result.get('energy_converged'),phase_converged=result.get('phase_converged'),phase64=result.get('phase64'))),flush=True)


if __name__=='__main__': main()
