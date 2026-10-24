"""Freeze retained benchmarks for a fresh campaign without importing old scores."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger',type=Path,default=Path('results/live/champions.json'))
    parser.add_argument('--controls',type=Path,default=Path('results/2026-10-22-dc-wide/summary.json'))
    parser.add_argument('--width-m',type=float,required=True)
    parser.add_argument('--contact-fraction',type=float,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from ballistic_lab.pipeline.contracts import SquareDevice
    ledger=json.loads(args.ledger.read_text(encoding='utf-8'))
    controls=json.loads(args.controls.read_text(encoding='utf-8'))
    records=[('synthetic-control',r) for r in controls if r['candidate']['key']=='D00']
    if len(records)!=1: raise ValueError('Exactly one D00 control required')
    records += [('retained-champion:'+key,value['candidate']) for key,value in sorted(ledger.items())]
    benchmarks=[]
    for role,row in records:
        c=row['candidate']
        device=SquareDevice(tuple(tuple(tuple(x) for x in poly) for poly in c['obstacles']),args.width_m,args.contact_fraction)
        benchmarks.append(dict(role=role,candidate=c,device=dict(obstacles=device.obstacles,width_m=device.width_m,contact_width_fraction=device.contact_width_fraction),evaluation_status='pending',score=None))
    payload=dict(schema=1,purpose='Matched re-evaluation inputs; prior scores are not new-model scores',benchmarks=benchmarks,source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.ledger,args.controls)})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as f: json.dump(payload,f,indent=2,allow_nan=False)
    print(f'Frozen {len(benchmarks)} benchmark inputs; no campaign launched')

if __name__=='__main__': main()
