"""Finite bulk scattering and infinitesimal angular-response diagnostics.
No imposed voltage-to-collimation law; no claimed electrical responsivity.
"""
import json,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gpu_trace import trace_gpu,polygon

from paths import OUT

def condition(polys,n,seed,mfp,spec=.8):
    strong=[];weak=[];p99=[]
    for port in (0,1):
        base=trace_gpu(polys,port,n=n,spread=1.,specularity=spec,seed=seed+port,raw=True,mfp=mfp)
        focused=trace_gpu(polys,port,n=n,spread=.35,specularity=spec,seed=seed+port,mfp=mfp)
        strong.append((focused[:,3]-focused[:,2])-(base[0][:,3]-base[0][:,2]))
        # s=sin(theta) is uniform for equilibrium cosine flux.
        # p_beta(s)=(1+beta*(1-2*s*s))/(2*(1+beta/3)); beta=0 is equilibrium.
        # derivative at beta=0 is weighting by h=2/3-2*s*s, exactly.
        rng=np.random.default_rng(seed+port);rng.uniform(-.3,.3,n);s=rng.uniform(-1,1,n)
        signs=(base[2]==3).astype(float)-(base[2]==2).astype(float)
        weak.append(np.mean(signs*(2/3-2*s*s)[None,:],axis=1))
        p99.append(np.quantile(base[1],.99,axis=1))
    return np.mean(strong,axis=0),np.mean(weak,axis=0),np.mean(p99,axis=0)

def main():
    start=time.perf_counter();checks=[]
    # Analytic probability of no bulk scattering for straight path across empty box.
    for mfp in [.5,2.,8.]:
        raw=trace_gpu([[]],0,n=131072,spread=0,mfp=mfp,raw=True,seed=7700)
        observed=float(np.mean(raw[3][0]==0));expected=float(np.exp(-2/mfp))
        assert abs(observed-expected)<.006
        checks.append(dict(test='exponential survival',mfp=mfp,observed=observed,expected=expected))
    poly=polygon([1.2,.6,0,0])
    for mfp in [.5,2.,8.]:
        matrix=np.array([trace_gpu([poly],k,n=65536,mfp=mfp,specularity=.8,seed=7800+k)[0] for k in range(4)])
        err=float(abs(matrix-matrix.T).max());assert err<.015
        checks.append(dict(test='finite-mfp reciprocity',mfp=mfp,max_error=err))
    learned=json.loads((OUT/'learning-results.json').read_text())
    params=[r['winners'][0] for r in learned['runs']]+[r['winners'][1] for r in learned['runs']]+[[1.2,.6,0,0]]
    names=['Learned 1','Learned 2','Learned 3','Random 1','Random 2','Random 3','Previous triangle','Empty control']
    # Zero-size edges retain batching shape while never intersecting rays.
    empty=[np.array([[0.,0.],[0.,0.],[0.,0.]])]
    polys=[polygon(x) for x in params]+[empty]
    results=[]
    for ratio in [.1,.25,.5,1.,2.,5.,10.,None]:
        mfp=None if ratio is None else 2*ratio
        samples=[condition(polys,32768,91000+17*k,mfp) for k in range(4)]
        values=np.array(samples)
        row=dict(mean_free_path_over_width=ratio,strong_mean=values[:,0].mean(axis=0).tolist(),
                 strong_seed_std=values[:,0].std(axis=0,ddof=1).tolist(),weak_mean=values[:,1].mean(axis=0).tolist(),
                 weak_seed_std=values[:,1].std(axis=0,ddof=1).tolist(),path_99_mean=values[:,2].mean(axis=0).tolist())
        results.append(row)
        print('MFP',ratio,'learned strong',np.mean(row['strong_mean'][:3]),'weak',np.mean(row['weak_mean'][:3]),flush=True)
        (OUT/'rf-scattering-checkpoint.json').write_text(json.dumps(results,indent=2))
    assert max(abs(r['weak_mean'][-1]) for r in results)<.01
    assert max(abs(r['strong_mean'][-1]) for r in results)<.02
    # Conditional Johnson-noise requirements, not a predicted detector.
    noise=[];kb=1.380649e-23;temp=300.;target=1e-12
    for resistance in [100.,1000.,10000.]:
        vn=np.sqrt(4*kb*temp*resistance)
        noise.append(dict(Rout_ohm=resistance,thermal_V_per_sqrtHz=float(vn),
                          required_V_per_W_for_1pW_NEPadmitted=float(vn/target)))
    summary=dict(names=names,params=params,checks=checks,scattering=results,conditional_noise_requirements=noise,
                 elapsed_seconds=time.perf_counter()-start,
                 scope='Angular sensitivity only. Weak derivative is per dimensionless beta, not per volt.')
    (OUT/'rf-screen-results.json').write_text(json.dumps(summary,indent=2))
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
    x=[r['mean_free_path_over_width'] for r in results[:-1]]
    for indices,name,color in [(slice(0,3),'Learned geometries','#147d92'),(slice(3,6),'Random-search winners','#bc6c25'),(slice(6,7),'Previous triangle','#777777')]:
        for ax,key in zip(axs,['strong_mean','weak_mean']):
            y=[100*np.mean(r[key][indices]) for r in results[:-1]]
            ax.plot(x,y,'o-',label=name,color=color)
            ax.axhline(100*np.mean(results[-1][key][indices]),color=color,alpha=.4,ls='--')
    axs[0].set(ylabel='Steering change (percentage points)',title='Previously optimized, large collimation change')
    axs[1].set(ylabel='Steering derivative (points per unit beta)',title='Infinitesimal smooth angular perturbation')
    for ax in axs:
        ax.set(xscale='log',xlabel='Mean free path / cavity width');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Bulk scattering stress test; dashed lines = no bulk scattering\nFixed wall specularity 0.8; no voltage or RF response assumed')
    fig.savefig(OUT/'rf-scattering.png',dpi=170);fig.savefig(OUT/'rf-scattering.pdf')
    print('DONE',json.dumps(summary),flush=True)

if __name__=='__main__':main()
