"""Numerical fixed-point convergence audit; not physical dynamical stability."""
import hashlib
import json
from pathlib import Path
from physics_layers.scalar_bound_feedback import observables


def main():
    source=Path('results/physics-reference/scalar-bound-feedback/result.json')
    data=json.loads(source.read_text())
    results=[]
    for row in data['rows']:
        if row['coupling_ev_per_electron'] != .2 or row['quadrature_tolerance'] != 1e-10:
            continue
        reference=row['reference_ev']
        root=row['onsite_ev']
        mapping=lambda u: .7+.2*(observables(u,reference,1e-10)[0]-data['neutral_charge'])
        slopes=[(mapping(root+d)-mapping(root-d))/(2*d) for d in (1e-4,1e-5,1e-6)]
        starts=[]
        for start in (.3,.7,1.1):
            u=start
            for iteration in range(200):
                new=mapping(u)
                if abs(new-u)<1e-10:
                    u=new
                    break
                u=new
            residual=abs(mapping(u)-u)
            starts.append(dict(start_ev=start,iterations=iteration+1,onsite_ev=u,residual_ev=residual,root_error_ev=abs(u-root)))
        if any(x['residual_ev']>1e-9 or x['root_error_ev']>1e-8 for x in starts):
            raise ArithmeticError(starts)
        results.append(dict(reference_ev=reference,derivative_steps_ev=[1e-4,1e-5,1e-6],map_slopes=slopes,starts=starts))
    out=Path('results/physics-reference/scalar-feedback-convergence')
    out.mkdir(parents=True,exist_ok=True)
    with (out/'result.json').open('x') as stream:
        json.dump(dict(scope=__doc__,input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=results),stream,indent=2)
    print(json.dumps(results,indent=2))

if __name__=='__main__':
    main()
