"""Count benchmark sites and dense-matrix storage without solving transport."""
import argparse
import hashlib
import json
from pathlib import Path
from ballistic_lab.pipeline.contracts import SquareDevice
from ballistic_lab.transport.quantum import LatticeRequest, build_system


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('benchmarks',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    payload=json.loads(args.benchmarks.read_text(encoding='utf-8'))
    rows=[]
    for item in payload['benchmarks']:
        d=item['device']
        device=SquareDevice(tuple(tuple(tuple(v) for v in p) for p in d['obstacles']),d['width_m'],d['contact_width_fraction'])
        system=build_system(device,LatticeRequest((2.5,)))
        n=len(system.sites)
        rows.append(dict(role=item['role'],key=item['candidate']['key'],sites=n,leads=len(system.leads),width_m=device.width_m,one_complex128_dense_matrix_bytes=16*n*n,site_ratio_to_51=n/51,dense_cubic_work_ratio_to_51=(n/51)**3))
    result=dict(source_sha256=hashlib.sha256(args.benchmarks.read_bytes()).hexdigest(),rows=rows,scope='Lattice construction only. Single-matrix storage is a lower bound, not total memory; cubic ratio is asymptotic work, not a runtime prediction. No charge, Poisson or transmission solve performed.')
    with args.output.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
    print(json.dumps(rows,indent=2))

if __name__=='__main__': main()
