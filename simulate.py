"""Reproducible classical geometry screen, NOT an electrical rectifier solver."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from paths import OUT
PORTS = ['Left', 'Right', 'Top', 'Bottom']

def shapes(kind, width=.6, height=.6, offset=0.):
    if kind == 'straight': return []
    if kind == 'triangle':
        return [np.array([[-width/2, offset+height/2], [width/2, offset+height/2], [0, offset-height/2]])]
    # Two wall-attached wedges: an asymmetric central constriction.
    return [np.array([[-1,.95],[-.25,.55],[-1,.35]]),
            np.array([[1,.95],[.25,.55],[1,.35]])]

def segments(polys):
    outer = np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
    starts = list(outer); ends = list(np.roll(outer,-1,axis=0))
    for p in polys:
        starts.extend(p); ends.extend(np.roll(p,-1,axis=0))
    return np.array(starts), np.array(ends)

def cross(a,b): return a[...,0]*b[...,1]-a[...,1]*b[...,0]

def trace(polys, port, n=8192, spread=1., specularity=1., seed=123, return_dest=False, mfp=None):
    """Uniform contact position, flux cosine angular law; spread<1 is imposed collimation.
    Square side=2 units; centered absorbing contacts width=.6 on all four sides.
    Directions are unit speed. Diffuse reflections obey the cosine flux law.
    """
    rng=np.random.default_rng(seed)
    u=rng.uniform(-.3,.3,n); theta=np.arcsin(rng.uniform(-spread,spread,n))
    normals=np.array([[1,0],[-1,0],[0,-1],[0,1]])
    normal=normals[port]; tangent=np.array([-normal[1],normal[0]])
    p=-normal[None,:]* (1-1e-9)+u[:,None]*tangent
    d=np.cos(theta)[:,None]*normal+np.sin(theta)[:,None]*tangent
    a,b=segments(polys); s=b-a
    sn=s/np.linalg.norm(s,axis=1)[:,None]
    norm=np.stack([-sn[:,1],sn[:,0]],axis=1)
    dest=np.full(n,-1); length=np.zeros(n); alive=np.arange(n)
    paths={i:[p[i].tolist()] for i in range(min(n,16))}
    for bounce in range(100000):
        if not len(alive): break
        pp=p[alive]; dd=d[alive]
        den=cross(dd[:,None,:],s[None,:,:])
        delta=a[None,:,:]-pp[:,None,:]
        with np.errstate(divide='ignore',invalid='ignore'):
            t=cross(delta,s[None,:,:])/den
            z=cross(delta,dd[:,None,:])/den
        t=np.where((t>1e-8)&(z>=-1e-10)&(z<=1+1e-10),t,np.inf)
        hit=np.argmin(t,axis=1); distance=t[np.arange(len(alive)),hit]
        if not np.isfinite(distance).all(): raise RuntimeError('Escaped boundary')
        bulk=np.zeros(len(alive),dtype=bool)
        if mfp is not None:
            flight=rng.exponential(mfp,len(alive))
            bulk=flight<distance
            distance=np.minimum(distance,flight)
        p[alive]+=distance[:,None]*dd; length[alive]+=distance
        for idx in alive[alive<16]: paths[int(idx)].append(p[idx].tolist())
        q=p[alive]
        contact=(~bulk)&(hit<4)&np.where((hit==0)|(hit==2),abs(q[:,0])<.3,abs(q[:,1])<.3)
        # Outer segments bottom,right,top,left -> terminal ids.
        mapping=np.array([3,1,2,0])
        dest[alive[contact]]=mapping[hit[contact]]
        keep=~contact; active=alive[keep]; nn=norm[hit[keep]]; old=dd[keep]
        reflected=old-2*np.sum(old*nn,axis=1)[:,None]*nn
        diffuse=(rng.random(len(active))>specularity)&(~bulk[keep])
        if diffuse.any():
            inward=nn[diffuse]*np.where(np.sum(old[diffuse]*nn[diffuse],axis=1)>0,-1,1)[:,None]
            tang=np.stack([-inward[:,1],inward[:,0]],axis=1)
            angle=np.arcsin(rng.uniform(-1,1,len(inward)))
            reflected[diffuse]=np.cos(angle)[:,None]*inward+np.sin(angle)[:,None]*tang
        if bulk.any():
            angle=rng.uniform(0,2*np.pi,int(bulk.sum()))
            reflected[bulk[keep]]=np.stack([np.cos(angle),np.sin(angle)],axis=1)
        d[active]=reflected; alive=active
    if len(alive): raise RuntimeError(f'{len(alive)} rays unresolved; increase bounce cap')
    probabilities=np.bincount(dest,minlength=4)/n
    if return_dest: return probabilities,length,paths,dest
    return probabilities,length,paths

def steering(polys,n=8192,spread=.35,specularity=1.,seed=123):
    p=np.array([trace(polys,k,n,spread,specularity,seed+k)[0] for k in (0,1)])
    return float(np.mean(p[:,3]-p[:,2])),p

def linear_output(p):
    # Symmetrize MC estimates to enforce exact reciprocity; diagonal ensures conservation.
    w=(p+p.T)/2; np.fill_diagonal(w,0)
    lap=np.diag(w.sum(axis=1))-w
    v=np.array([.5,-.5,0.,0.])
    v[2:]=np.linalg.solve(lap[2:,2:],-lap[2:,:2]@v[:2])
    reverse=-v
    return float(v[2]-v[3]),float((v[2]-v[3]+reverse[2]-reverse[3])/2)

def main():
    kinds=['straight','triangle','constriction']; rows=[]; matrices=[]
    fig,axs=plt.subplots(2,3,figsize=(13,8),layout='constrained')
    for col,kind in enumerate(kinds):
        poly=shapes(kind)
        p=np.array([trace(poly,k,n=32768,seed=500+k)[0] for k in range(4)])
        matrices.append(p)
        eq,_=steering(poly,n=32768,spread=1.,seed=800)
        focus,prob=steering(poly,n=32768,spread=.35,seed=800)
        lin,dc=linear_output(p)
        rows.append(dict(geometry=kind,equilibrium_angular_steering=eq,collimated_steering=focus,
                         steering_change=focus-eq,raw_reciprocity_max=float(abs(p-p.T).max()),
                         linear_transverse_ratio=lin,linear_DC_ratio=dc,probabilities=p.tolist()))
        ax=axs[0,col]; a,b=segments(poly)
        for aa,bb in zip(a,b): ax.plot(*np.array([aa,bb]).T,color='black',lw=2)
        for k,xy in enumerate([([-1,-1],[-.3,.3]),([1,1],[-.3,.3]),([-.3,.3],[1,1]),([-.3,.3],[-1,-1])]):
            ax.plot(*xy,color='#45b66d',lw=5,zorder=5)
        for port,color in [(0,'#168aad'),(1,'#ef8354')]:
            _,_,paths=trace(poly,port,n=32,spread=.35,seed=42+port)
            for path in list(paths.values())[:6]: ax.plot(*np.array(path).T,color=color,alpha=.4,lw=.8)
        ax.set(xlim=(-1.08,1.08),ylim=(-1.08,1.08),aspect='equal',title=kind.capitalize(),xlabel='Normalized x',ylabel='Normalized y')
        ax=axs[1,col]
        im=ax.imshow(p,vmin=0,vmax=1,cmap='Blues')
        for i in range(4):
            for j in range(4): ax.text(j,i,f'{p[i,j]:.3f}',ha='center',va='center')
        ax.set(xticks=range(4),xticklabels=PORTS,yticks=range(4),yticklabels=PORTS,xlabel='Exit terminal',ylabel='Injection terminal',title='Equilibrium angular transmission')
    fig.suptitle('Ballistic geometry screen: trajectories and reciprocal scattering\nClassical hard-wall rays; illustrative geometry, no calibrated voltage response')
    fig.savefig(OUT/'geometries.png',dpi=170); fig.savefig(OUT/'geometries.pdf'); plt.close(fig)
    # Coarse multi-parameter search. Common random numbers reduce comparison noise.
    sweep=[]
    for width in [.3,.6,.9,1.2]:
        for height in [.3,.6,.9]:
            for offset in [-.25,0,.25]:
                poly=shapes('triangle',width,height,offset)
                eq,_=steering(poly,n=4096,spread=1.)
                focused,_=steering(poly,n=4096,spread=.35)
                sweep.append(dict(width=width,height=height,offset=offset,change=focused-eq))
    best=max(sweep,key=lambda r:r['change']); poly=shapes('triangle',best['width'],best['height'],best['offset'])
    holdout=[]
    for spec in [1.,.8,.5,0.]:
        changes=[]
        for seed in range(4):
            eq,_=steering(poly,n=32768,spread=1.,specularity=spec,seed=2000+10*seed)
            focus,_=steering(poly,n=32768,spread=.35,specularity=spec,seed=2000+10*seed)
            changes.append(focus-eq)
        holdout.append(dict(specularity=spec,mean=float(np.mean(changes)),seed_std=float(np.std(changes,ddof=1)),samples=changes))
    # Mirror reverses steering; empty junction is symmetry control.
    mirror=[p*np.array([1,-1]) for p in poly]
    original=steering(poly,n=65536,seed=7000)[0]
    mirrored=steering(mirror,n=65536,seed=7000)[0]
    checks=dict(max_reciprocity_error=max(r['raw_reciprocity_max'] for r in rows),mirror_sum=original+mirrored,
                straight_collimated_steering=rows[0]['collimated_steering'],linear_DC_max=max(abs(r['linear_DC_ratio']) for r in rows))
    assert checks['max_reciprocity_error']<.02
    assert abs(checks['mirror_sum'])<.02
    assert abs(checks['straight_collimated_steering'])<.02
    assert checks['linear_DC_max']<1e-12
    result=dict(model='Classical geometric collimation sensitivity; not DC voltage or efficiency',baselines=rows,sweep=sweep,best=best,holdout=holdout,checks=checks)
    (OUT/'results.json').write_text(json.dumps(result,indent=2))
    fig,ax=plt.subplots(figsize=(8,4.5),layout='constrained')
    ax.errorbar([r['specularity'] for r in holdout],[100*r['mean'] for r in holdout],yerr=[100*r['seed_std'] for r in holdout],fmt='o-',capsize=4)
    ax.set(xlabel='Probability of specular wall reflection',ylabel='Change in bottom-minus-top probability (points)',title='Selected triangle: sensitivity to imposed angular collimation\nError bars: seed standard deviation, not fabrication uncertainty')
    ax.grid(alpha=.25);fig.savefig(OUT/'robustness.png',dpi=170);plt.close(fig)
    print(json.dumps(dict(baselines=rows,best=best,holdout=holdout,checks=checks),indent=2))

if __name__=='__main__': main()
