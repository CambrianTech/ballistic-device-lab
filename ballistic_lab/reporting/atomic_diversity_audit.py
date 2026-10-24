"""Audit atomic identity of one completed generation without solving transport."""
import argparse
import hashlib
import json
from pathlib import Path
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system
from ballistic_lab.experiments.coverage import CoveragePlan

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('snapshot',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 s=json.loads(a.snapshot.read_text());rows=[];groups={}
 for r in s['rows']:
  c=r['candidate']
  if c['round']!=s['round']:continue
  system=build_system(SquareDevice(c['obstacles'],CoveragePlan().width_m,.3),LatticeRequest((.9,)))
  identity=dict(sites=[(str(x.family),tuple(int(v) for v in x.tag)) for x in system.sites],edges=list(system.graph),interfaces=[list(map(int,x)) for x in system.lead_interfaces])
  digest=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();groups.setdefault(digest,[]).append(c['key'])
  rows.append(dict(key=c['key'],family=c['family'],sites=len(system.sites),atomic_sha256=digest))
 result=dict(snapshot=str(a.snapshot),snapshot_sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),generation=s['round'],candidates=len(rows),distinct_atomic_lattices=len(groups),duplicates=[x for x in groups.values() if len(x)>1],rows=rows,scope='Exact site, graph and lead-interface identity under the fixed lattice builder; not transport diversity or physical novelty.')
 with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 print(result['candidates'],result['distinct_atomic_lattices'])
if __name__=='__main__':main()
