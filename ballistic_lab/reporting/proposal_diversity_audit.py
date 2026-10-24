"""Audit exact proposal diversity and refinement coverage from a frozen snapshot."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 s=json.loads(a.snapshot.read_text());rows=s['rows'];fingerprints=[];groups={}
 for r in rows:
  c=r['candidate'];fingerprints.append(hashlib.sha256(json.dumps(c['obstacles'],sort_keys=True).encode()).hexdigest())
  strategy=c.get('proposal_strategy','unrecorded');g=groups.setdefault(strategy,dict(proposed=0,converged=0,origins={}))
  g['proposed']+=1;g['converged']+=int(bool(r.get('energy_converged') and r.get('phase_converged')))
  origin='mutation' if c['origin'].startswith('mutation of ') else 'fresh';g['origins'][origin]=g['origins'].get(origin,0)+1
 counts=Counter(fingerprints)
 report=dict(snapshot=str(a.snapshot),sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),round=s['round'],candidates=len(rows),unique_exact_polygon_encodings=len(counts),duplicate_encodings=sum(n-1 for n in counts.values()),by_strategy=groups,limitations='Exact polygon identity only, not atomic-lattice or behavioral novelty. Sequential strategies share history; counts do not establish strategy superiority.')
 with a.output.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
