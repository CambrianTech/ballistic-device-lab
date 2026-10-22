"""Search infinitesimal angular response under bulk scattering; retain diverse finalists."""
import json
import numpy as np
from learn_search import forest,propose
from gpu_trace import sample,polygon,trace_gpu
from rf_screen import OUT

def evaluate(x,seed=123,n=8192,mfp=2.):
    scores=[]
    for start in range(0,len(x),32):
        polys=[polygon(z) for z in x[start:start+32]];v=[]
        for port in [0,1]:
            p=trace_gpu(polys,port,n=n,mfp=mfp,specularity=.8,seed=seed+port,raw=True)
            rng=np.random.default_rng(seed+port);rng.uniform(-.3,.3,n);s=rng.uniform(-1,1,n)
            sign=(p[2]==3).astype(float)-(p[2]==2).astype(float)
            v.append(np.mean(sign*(2/3-2*s*s)[None,:],axis=1))
        scores.extend(np.mean(v,axis=0).tolist())
    return np.array(scores)

def main():
    rng=np.random.default_rng(314159);x=sample(rng,64);y=evaluate(x,seed=81234)
    xr=x.copy();yr=y.copy();records=[]
    for k in range(4):
        a=propose(forest(100+k).fit(x,y),x,y,rng);r=sample(rng,64)
        ay=evaluate(a,seed=82000+k);ry=evaluate(r,seed=82000+k)
        x=np.concatenate([x,a]);y=np.r_[y,ay];xr=np.concatenate([xr,r]);yr=np.r_[yr,ry]
        records.append(dict(budget=len(y),active=float(y.max()),random=float(yr.max())))
        print(records[-1],flush=True)
    # Preserve best and a geometrically distinct runner-up, plus controls.
    order=np.argsort(y)[::-1];best=x[order[0]]
    other=next(x[i] for i in order[1:] if np.linalg.norm(x[i]-best)>.15)
    old=json.loads((OUT/'learning-results.json').read_text())['runs'][0]['winners'][0]
    finalists=np.array([best,other,xr[yr.argmax()],old,[1.2,.6,0,0]])
    names=['Robust best','Diverse runner-up','Equal-budget random','Prior learned','Simple triangle']
    (OUT/'robust-frozen.json').write_text(json.dumps(dict(names=names,geometry=finalists.tolist()),indent=2))
    # Fresh seed validation at three scattering regimes, without reselection.
    validations=[]
    for ratio in [.5,1.,2.]:
        scores=np.array([evaluate(finalists,seed=87000+k,n=65536,mfp=2*ratio) for k in range(4)])
        validations.append(dict(mfp_over_width=ratio,mean=scores.mean(axis=0).tolist(),seed_std=scores.std(axis=0,ddof=1).tolist()))
    # Illustrative fabrication stress: independent relative width/height perturbations
    # of +/-2%, vertical offset +/- .01 and normalized tip skew +/- .02. Not calibrated.
    tolerance=[]
    for z in finalists:
        perturbed=np.tile(z,(32,1));perturbed[:,:2]*=rng.uniform(.98,1.02,(32,2))
        perturbed[:,2]+=rng.uniform(-.01,.01,32);perturbed[:,3]+=rng.uniform(-.02,.02,32)
        vals=evaluate(perturbed,seed=89000,n=16384)
        tolerance.append(dict(mean=float(vals.mean()),p10=float(np.quantile(vals,.1)),minimum=float(vals.min())))
    result=dict(names=names,finalists=finalists.tolist(),history=records,validation=validations,tolerance=tolerance,
                training=dict(active_x=x.tolist(),active_y=y.tolist(),random_x=xr.tolist(),random_y=yr.tolist()),
                scope='One search repeat, angular response derivative per beta, not electrical rectification')
    (OUT/'robust-search-results.json').write_text(json.dumps(result,indent=2));print('DONE',flush=True)

if __name__=='__main__':main()
