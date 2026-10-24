"""Compare matched completed discovery horizons without changing workers."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def validate_pair(first, second):
    """Refuse misleading shared benchmarks before creating any report."""
    for key in ('round', 'objective', 'control', 'retained_champion'):
        if key not in first or key not in second or first[key] != second[key]:
            raise ValueError('Unmatched or missing comparison field: ' + key)
    for snapshot in (first, second):
        keys = [r['candidate']['key'] for r in snapshot['rows']]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate candidate identity')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('first',type=Path);p.add_argument('second',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args(); summaries=[]; populations=[]
    validate_pair(json.loads(a.first.read_text()), json.loads(a.second.read_text()))
    for path in (a.first,a.second):
        s=json.loads(path.read_text())
        q=[r for r in s['rows'] if r.get('energy_converged') and r.get('phase_converged') and r.get('phase64')]
        best=max(q,key=lambda r:r['phase64']['dc_power_w']) if q else None
        summaries.append(dict(source=path.as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),round=s['round'],evaluated=len(s['rows']),qualified=len(q),qualified_families=dict(Counter(r['candidate']['family'] for r in q)),best=best,control=s['control'],retained=s['retained_champion']))
        populations.append({r['candidate']['key']:r['candidate'] for r in s['rows']})
    if summaries[0]['round']!=summaries[1]['round']:raise ValueError('Unmatched horizons')
    shared=set(populations[0]) & set(populations[1])
    identical=sum(populations[0][k]==populations[1][k] for k in shared)
    with a.output.open('x') as f:json.dump(dict(scope='Single-seed fixed-potential policy comparison; candidate counts are not CPU budgets.',identical_candidate_records=identical,arms=summaries),f,indent=2)
    for s in summaries: print(s['source'],s['evaluated'],s['qualified'],s['qualified_families'],s['best']['phase64']['dc_v'])
    print('identical candidate records',identical)

if __name__=='__main__':main()

