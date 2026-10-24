"""Synthetic scalar Hartree closure, not a graphene Poisson model."""
import json
import hashlib
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import expit
from scipy.constants import Boltzmann, elementary_charge, h


def observables(u, reference, tolerance):
    kt = Boltzmann*150/elementary_charge
    f = lambda e, mu: expit((mu-e)/kt)
    density = lambda e: np.sqrt(max(0,4-e*e))/(np.pi*(4-e*e+u*u))
    pole = np.sqrt(4+u*u)
    weight = u/pole
    charge = quad(lambda e: density(e)*(f(e,.2)+f(e,-.1)), -2, 2, epsabs=tolerance, epsrel=tolerance)[0]+2*weight*f(pole,reference)
    current = 2*elementary_charge**2/h*quad(lambda e: (4-e*e)/(4-e*e+u*u)*(f(e,.2)-f(e,-.1)), -2, 2, epsabs=tolerance, epsrel=tolerance)[0]
    return charge,current


def main():
    out=Path('results/physics-reference/scalar-bound-feedback')
    if (out/'result.json').exists():
        raise FileExistsError(out/'result.json')
    u0=.7
    pole=np.sqrt(4+u0*u0)
    neutral=observables(u0,pole,1e-10)[0]
    rows=[]
    for coupling in (0,.2):
        for reference in (pole-.02,pole+.02):
            for tolerance in (1e-8,1e-10):
                residual=lambda u: u-u0-coupling*(observables(u,reference,tolerance)[0]-neutral)
                # n in [0,2], n0 in [0,2] ensures a root in u0 +/- 2g.
                u=u0 if coupling==0 else brentq(residual,.3,1.1,xtol=1e-11)
                n,current=observables(u,reference,tolerance)
                error=abs(residual(u))
                if error>1e-9: raise ArithmeticError(error)
                rows.append(dict(coupling_ev_per_electron=coupling,reference_ev=float(reference),quadrature_tolerance=tolerance,onsite_ev=u,charge_electrons=n,current_a=current,residual_ev=error))
    out.mkdir(parents=True,exist_ok=True)
    with (out/'result.json').open('x') as stream:
        json.dump(dict(scope=__doc__,equation='U=0.7+g*(n(U,reference)-n0)',neutral_charge=neutral,temperature_k=150,chemical_potentials_ev=[.2,-.1],source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows),stream,indent=2)
    for g in (0,.2):
        pair=[r for r in rows if r['coupling_ev_per_electron']==g and r['quadrature_tolerance']==1e-10]
        print(g,'potential spread',pair[1]['onsite_ev']-pair[0]['onsite_ev'],'current spread',pair[1]['current_a']-pair[0]['current_a'])

if __name__=='__main__':
    main()
