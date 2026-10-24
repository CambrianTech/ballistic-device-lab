"""Audit immutable fresh-campaign snapshots without touching the worker."""
import argparse
import hashlib
import json
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 records=[]
 for path in sorted(a.root.glob('round-*.json')):
  s=json.loads(path.read_text()); qualified=[r for r in s['rows'] if r.get('energy_converged') and r.get('phase_converged') and r.get('phase64')]
  best=max(qualified,key=lambda r:r['phase64']['dc_power_w']) if qualified else None
  expected=max([s['retained_champion']]+qualified,key=lambda r:r['phase64']['dc_power_w'])
  if s['champion']['candidate']['key']!=expected['candidate']['key']:raise ValueError('Champion mismatch '+str(path))
  keys=[r['candidate']['key'] for r in s['rows']]
  if len(keys)!=len(set(keys)):raise ValueError('Duplicate candidate identity')
  records.append(dict(round=s['round'],evaluated=len(keys),qualified=len(qualified),source=path.as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),best=best,retained=s['retained_champion'],control=s['control'],champion_check_passed=True))
 with a.output.open('x',encoding='utf-8') as f:json.dump(dict(scope='Fixed-potential simulated DC; numerical convergence is not physical validation or novelty.',rounds=records),f,indent=2,allow_nan=False)
if __name__=='__main__':main()
