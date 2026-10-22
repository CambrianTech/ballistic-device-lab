"""Bounded active-learning benchmark with equal simulation budgets and frozen winners."""
from pathlib import Path
import json,time
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import r2_score,mean_absolute_error
from sklearn.inspection import permutation_importance
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gpu_trace import evaluate,sample,BOUNDS

from paths import OUT
NAMES=['width','height','vertical offset','tip skew']
def forest(seed):return ExtraTreesRegressor(n_estimators=128,min_samples_leaf=2,bootstrap=True,random_state=seed,n_jobs=2)
def log(data):
    with (OUT/'learning-data.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
def score(x,seed,tag,n=4096):
    y=evaluate(x,n=n,seed=seed)
    log(dict(tag=tag,seed=seed,rays_per_condition=n,x=x.tolist(),y=y.tolist()))
    return y
def propose(model,x,y,rng):
    # Half global exploration, half local proposals around known high performers.
    global_x=sample(rng,4096)
    elite=x[np.argsort(y)[-8:]]
    local=elite[rng.integers(len(elite),size=4096)]+rng.normal(size=(4096,4))*.10*np.ptp(BOUNDS,axis=1)
    local=np.clip(local,BOUNDS[:,0],BOUNDS[:,1])
    pool=np.concatenate([global_x,local])
    pred=np.array([tree.predict(pool) for tree in model.estimators_])
    utility=pred.mean(axis=0)+.75*pred.std(axis=0)
    selected=[];scale=np.ptp(BOUNDS,axis=1)
    for j in np.argsort(utility)[::-1]:
        z=pool[j]
        if np.min(np.linalg.norm((x-z)/scale,axis=1))<.035:continue
        if selected and np.min(np.linalg.norm((np.array(selected)-z)/scale,axis=1))<.06:continue
        selected.append(z)
        if len(selected)==48:break
    assert len(selected)==48
    return np.concatenate([selected,sample(rng,16)])

def main():
    started=time.perf_counter()
    validation=json.loads((OUT/'gpu-validation.json').read_text())
    if validation['speedup']<2:raise RuntimeError('GPU throughput gate failed')
    # Fresh run outputs; never overwrite the original geometry screen.
    if (OUT/'learning-data.jsonl').exists():
        return resume_frozen()
    rng=np.random.default_rng(8675309)
    train=sample(rng,192);test=sample(rng,128)
    y=score(train,12300,'pilot-training');yt=score(test,22300,'pilot-heldout',8192)
    model=forest(17).fit(train,y)
    r2=float(r2_score(yt,model.predict(test)))
    pilot=dict(r2=r2,mae=float(mean_absolute_error(yt,model.predict(test))))
    (OUT/'pilot.json').write_text(json.dumps(pilot,indent=2))
    print('PILOT',json.dumps(pilot),flush=True)
    if r2<.25:raise RuntimeError('Surrogate failed predictive gate; no expanded search launched')
    # Diagnostic feature ranking, no dimension removed from the actual search.
    imp=permutation_importance(model,test,yt,n_repeats=8,random_state=67,n_jobs=2)
    ranking=np.argsort(imp.importances_mean)[::-1]
    reduced=forest(17).fit(train[:,ranking[:2]],y)
    feature=dict(names=NAMES,permutation_r2_drop=imp.importances_mean.tolist(),
                 permutation_std=imp.importances_std.tolist(),two_features=[NAMES[i] for i in ranking[:2]],
                 reduced_test_r2=float(r2_score(yt,reduced.predict(test[:,ranking[:2]]))))
    results=[]
    for rep in range(3):
        rng=np.random.default_rng(41000+rep)
        x0=sample(rng,64);y0=score(x0,31000+rep,'shared-initial-'+str(rep))
        xa=x0.copy();ya=y0.copy();xr=x0.copy();yr=y0.copy()
        history=[dict(budget=64,active=float(ya.max()),random=float(yr.max()))]
        for round_no in range(5):
            fit=forest(rep*100+round_no).fit(xa,ya)
            newa=propose(fit,xa,ya,rng);newr=sample(rng,64)
            # Same simulator seed for both arms at each stage.
            seed=51000+rep*100+round_no
            va=score(newa,seed,f'active-{rep}-{round_no}')
            vr=score(newr,seed,f'random-{rep}-{round_no}')
            xa=np.concatenate([xa,newa]);ya=np.concatenate([ya,va])
            xr=np.concatenate([xr,newr]);yr=np.concatenate([yr,vr])
            history.append(dict(budget=len(ya),active=float(ya.max()),random=float(yr.max())))
            print('ROUND',rep,round_no,history[-1],flush=True)
        # Select using training data only; then freeze and evaluate new independent seeds.
        winners=np.array([xa[ya.argmax()],xr[yr.argmax()],[1.2,.6,0,0]])
        frozen=dict(rep=rep,winners=winners.tolist(),history=history)
        (OUT/f'frozen-winners-{rep}.json').write_text(json.dumps(frozen,indent=2))
        holdout=np.array([score(winners,71000+rep*100+k,f'holdout-{rep}-{k}',65536) for k in range(4)])
        frozen.update(holdout=holdout.tolist(),mean=holdout.mean(axis=0).tolist(),std=holdout.std(axis=0,ddof=1).tolist())
        results.append(frozen)
        (OUT/'learning-checkpoint.json').write_text(json.dumps(results,indent=2))
    finish(results,pilot,feature,time.perf_counter()-started)

def finish(results,pilot,feature,elapsed):
    summary=dict(pilot=pilot,feature_diagnostics=feature,runs=results,
                 elapsed_seconds=elapsed,
                 objective='mean collimation-induced steering change at specularity 1 and .8; not efficiency',
                 active_minus_random=[r['mean'][0]-r['mean'][1] for r in results])
    (OUT/'learning-results.json').write_text(json.dumps(summary,indent=2))
    fig,axes=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
    for rep,r in enumerate(results):
        for arm,color in [('active','#147d92'),('random','#bc6c25')]:
            axes[0].plot([h['budget'] for h in r['history']],[100*h[arm] for h in r['history']],color=color,alpha=.65,label=arm if rep==0 else None)
        axes[1].errorbar(np.arange(3)+(rep-1)*.16,100*np.array(r['mean']),yerr=100*np.array(r['std']),fmt='o',capsize=3,label=f'Repeat {rep+1}')
    axes[0].set(xlabel='Geometry evaluations per arm',ylabel='Best training score (percentage points)',title='Equal-budget searches (3 independent repeats)');axes[0].legend()
    axes[1].set(xticks=range(3),xticklabels=['Learned search','Random search','Previous triangle'],ylabel='Fresh-seed score (percentage points)',title='Frozen winners; seed standard deviation bars');axes[1].legend()
    fig.suptitle('Learning geometry sensitivity in a classical ray model — not rectifier efficiency')
    fig.savefig(OUT/'learning-results.png',dpi=170);fig.savefig(OUT/'learning-results.pdf')
    print('DONE',json.dumps(summary),flush=True)

def resume_frozen():
    """Resume missing holdout samples only; never reselect using holdout information."""
    records=[json.loads(s) for s in (OUT/'learning-data.jsonl').read_text().splitlines()]
    by_tag={r['tag']:r for r in records}
    train=np.array(by_tag['pilot-training']['x']);y=np.array(by_tag['pilot-training']['y'])
    test=np.array(by_tag['pilot-heldout']['x']);yt=np.array(by_tag['pilot-heldout']['y'])
    model=forest(17).fit(train,y)
    imp=permutation_importance(model,test,yt,n_repeats=8,random_state=67,n_jobs=2)
    ranking=np.argsort(imp.importances_mean)[::-1]
    reduced=forest(17).fit(train[:,ranking[:2]],y)
    feature=dict(names=NAMES,permutation_r2_drop=imp.importances_mean.tolist(),permutation_std=imp.importances_std.tolist(),
                 two_features=[NAMES[i] for i in ranking[:2]],reduced_test_r2=float(r2_score(yt,reduced.predict(test[:,ranking[:2]]))))
    results=[]
    for rep in range(3):
        frozen=json.loads((OUT/f'frozen-winners-{rep}.json').read_text())
        winners=np.array(frozen['winners']);values=[]
        for k in range(4):
            tag=f'holdout-{rep}-{k}'
            if tag in by_tag:values.append(by_tag[tag]['y'])
            else:values.append(score(winners,71000+rep*100+k,tag,65536))
        holdout=np.array(values)
        frozen.update(holdout=holdout.tolist(),mean=holdout.mean(axis=0).tolist(),std=holdout.std(axis=0,ddof=1).tolist())
        results.append(frozen)
    finish(results,json.loads((OUT/'pilot.json').read_text()),feature,None)

if __name__=='__main__':main()
